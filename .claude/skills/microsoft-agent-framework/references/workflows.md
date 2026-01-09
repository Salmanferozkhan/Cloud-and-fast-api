# Microsoft Agent Framework Workflows

Workflows enable complex multi-agent orchestration using graph-based execution with streaming, checkpointing, and human-in-the-loop capabilities.

## Table of Contents

- [Basic Workflow Structure](#basic-workflow-structure)
- [Executors and Edges](#executors-and-edges)
- [Using Agents in Workflows](#using-agents-in-workflows)
- [Streaming](#streaming)
- [Fan-Out and Fan-In](#fan-out-and-fan-in)
- [Conditional Routing](#conditional-routing)
- [Looping](#looping)
- [Checkpointing](#checkpointing)
- [Human-in-the-Loop](#human-in-the-loop)
- [Writer-Critic Pattern](#writer-critic-pattern)
- [Sub-Workflows](#sub-workflows)
- [Declarative Workflows](#declarative-workflows)

## Basic Workflow Structure

```csharp
using Microsoft.Agents.Workflows;

// Define a workflow
var workflow = new WorkflowBuilder()
    .AddExecutor("step1", async (input) =>
    {
        return $"Processed: {input}";
    })
    .AddExecutor("step2", async (input) =>
    {
        return $"Final: {input}";
    })
    .AddEdge("step1", "step2")
    .SetEntryPoint("step1")
    .Build();

var result = await workflow.RunAsync("Hello");
```

## Executors and Edges

Executors are processing units; edges define data flow:

```csharp
var workflow = new WorkflowBuilder()
    // Executors process data
    .AddExecutor("validate", ValidateInput)
    .AddExecutor("transform", TransformData)
    .AddExecutor("save", SaveToDatabase)

    // Edges define flow
    .AddEdge("validate", "transform")
    .AddEdge("transform", "save")

    .SetEntryPoint("validate")
    .Build();
```

## Using Agents in Workflows

Integrate AI agents as workflow executors:

```csharp
var researchAgent = client.GetChatClient("gpt-4o")
    .CreateAIAgent(instructions: "Research topics thoroughly.");

var summaryAgent = client.GetChatClient("gpt-4o-mini")
    .CreateAIAgent(instructions: "Summarize research findings.");

var workflow = new WorkflowBuilder()
    .AddAgentExecutor("research", researchAgent)
    .AddAgentExecutor("summarize", summaryAgent)
    .AddEdge("research", "summarize")
    .SetEntryPoint("research")
    .Build();

var result = await workflow.RunAsync("Explain quantum computing");
```

## Streaming

Enable real-time event streaming:

```csharp
var workflow = new WorkflowBuilder()
    .AddExecutor("process", ProcessData)
    .EnableStreaming()
    .Build();

await foreach (var evt in workflow.StreamAsync("input"))
{
    switch (evt)
    {
        case ExecutorStartEvent start:
            Console.WriteLine($"Starting: {start.ExecutorName}");
            break;
        case ExecutorCompleteEvent complete:
            Console.WriteLine($"Complete: {complete.ExecutorName}");
            break;
        case TokenEvent token:
            Console.Write(token.Text);
            break;
    }
}
```

## Fan-Out and Fan-In

Parallel processing pattern:

```csharp
var workflow = new WorkflowBuilder()
    // Entry point
    .AddExecutor("split", SplitWork)

    // Parallel executors (fan-out)
    .AddExecutor("worker1", ProcessPart1)
    .AddExecutor("worker2", ProcessPart2)
    .AddExecutor("worker3", ProcessPart3)

    // Aggregator (fan-in)
    .AddExecutor("combine", CombineResults)

    // Fan-out edges
    .AddEdge("split", "worker1")
    .AddEdge("split", "worker2")
    .AddEdge("split", "worker3")

    // Fan-in edges
    .AddEdge("worker1", "combine")
    .AddEdge("worker2", "combine")
    .AddEdge("worker3", "combine")

    .SetEntryPoint("split")
    .Build();
```

## Conditional Routing

Dynamic routing based on executor output:

```csharp
var workflow = new WorkflowBuilder()
    .AddExecutor("classify", ClassifyInput)
    .AddExecutor("handleSimple", HandleSimpleCase)
    .AddExecutor("handleComplex", HandleComplexCase)

    // Conditional edges
    .AddConditionalEdge("classify", output =>
        output.Contains("simple") ? "handleSimple" : "handleComplex")

    .SetEntryPoint("classify")
    .Build();
```

### Switch-Case Routing

```csharp
.AddSwitchEdge("router", new Dictionary<string, string>
{
    ["typeA"] = "handlerA",
    ["typeB"] = "handlerB",
    ["typeC"] = "handlerC",
    ["default"] = "defaultHandler"
})
```

### Multi-Selection Routing

One executor triggers multiple downstream:

```csharp
.AddMultiSelectEdge("analyzer", output =>
{
    var targets = new List<string>();
    if (output.NeedsReview) targets.Add("reviewer");
    if (output.NeedsNotification) targets.Add("notifier");
    if (output.NeedsArchive) targets.Add("archiver");
    return targets;
})
```

## Looping

Create iteration loops:

```csharp
var workflow = new WorkflowBuilder()
    .AddExecutor("generate", GenerateContent)
    .AddExecutor("evaluate", EvaluateQuality)

    // Loop back if quality insufficient
    .AddConditionalEdge("evaluate", result =>
        result.Score < 0.8 ? "generate" : "output")

    .AddExecutor("output", FinalizeOutput)
    .SetEntryPoint("generate")
    .SetMaxIterations(5) // Safety limit
    .Build();
```

## Checkpointing

Save and restore workflow state:

```csharp
var workflow = new WorkflowBuilder()
    .AddExecutor("step1", Step1)
    .AddExecutor("step2", Step2)
    .AddExecutor("step3", Step3)
    .EnableCheckpointing()
    .Build();

// Run with checkpointing
var runner = workflow.CreateRunner();
await runner.RunToCheckpointAsync("step2", input);

// Save state
var checkpoint = runner.SaveCheckpoint();
await File.WriteAllTextAsync("checkpoint.json", checkpoint.ToJson());

// Later: Resume from checkpoint
var savedCheckpoint = Checkpoint.FromJson(
    await File.ReadAllTextAsync("checkpoint.json"));
var newRunner = workflow.CreateRunner(savedCheckpoint);
await newRunner.ResumeAsync();
```

### Checkpoint with Rehydration

Restore workflow in new process:

```csharp
// Original process saves checkpoint
var checkpoint = runner.SaveCheckpoint();

// New process rehydrates
var workflow = BuildWorkflow(); // Same workflow definition
var runner = workflow.Rehydrate(checkpoint);
await runner.ResumeAsync();
```

## Human-in-the-Loop

Pause workflow for user input:

```csharp
var workflow = new WorkflowBuilder()
    .AddExecutor("prepare", PrepareProposal)

    // Human review point
    .AddInputPort("review", async (proposal) =>
    {
        Console.WriteLine($"Review proposal: {proposal}");
        Console.Write("Approve? (y/n): ");
        var response = Console.ReadLine();
        return new ReviewResult
        {
            Approved = response?.ToLower() == "y",
            Comments = response
        };
    })

    .AddExecutor("finalize", FinalizeProposal)
    .AddExecutor("revise", ReviseProposal)

    .AddEdge("prepare", "review")
    .AddConditionalEdge("review", result =>
        result.Approved ? "finalize" : "revise")
    .AddEdge("revise", "review") // Loop back for re-review

    .SetEntryPoint("prepare")
    .Build();
```

### Checkpoint with Human-in-the-Loop

Combine checkpointing with human review:

```csharp
var workflow = new WorkflowBuilder()
    .AddExecutor("analyze", AnalyzeData)
    .AddCheckpoint("before_review") // Save state here
    .AddInputPort("human_review", GetHumanFeedback)
    .AddExecutor("process", ProcessWithFeedback)
    .EnableCheckpointing()
    .Build();
```

## Writer-Critic Pattern

Iterative refinement with quality gates:

```csharp
var writerAgent = client.GetChatClient("gpt-4o")
    .CreateAIAgent(instructions: "Write high-quality content.");

var criticAgent = client.GetChatClient("gpt-4o")
    .CreateAIAgent(instructions: "Critique content, suggest improvements.");

var workflow = new WorkflowBuilder()
    .AddAgentExecutor("writer", writerAgent)
    .AddAgentExecutor("critic", criticAgent)
    .AddExecutor("evaluator", EvaluateScore)

    .AddEdge("writer", "critic")
    .AddEdge("critic", "evaluator")

    // Quality gate
    .AddConditionalEdge("evaluator", result =>
        result.Score >= 0.9 ? "output" : "writer")

    .AddExecutor("output", Finalize)
    .SetEntryPoint("writer")
    .SetMaxIterations(3)
    .Build();
```

## Sub-Workflows

Compose workflows hierarchically:

```csharp
// Define sub-workflow
var validationWorkflow = new WorkflowBuilder()
    .AddExecutor("check_format", CheckFormat)
    .AddExecutor("check_content", CheckContent)
    .AddEdge("check_format", "check_content")
    .SetEntryPoint("check_format")
    .Build();

// Use in parent workflow
var mainWorkflow = new WorkflowBuilder()
    .AddExecutor("input", GetInput)
    .AddSubWorkflow("validate", validationWorkflow)
    .AddExecutor("process", ProcessValidated)
    .AddEdge("input", "validate")
    .AddEdge("validate", "process")
    .SetEntryPoint("input")
    .Build();
```

## Declarative Workflows

Define workflows in YAML/JSON:

```yaml
# workflow.yaml
name: content-pipeline
entry_point: fetch

executors:
  fetch:
    type: function
    handler: FetchContent
  process:
    type: agent
    model: gpt-4o-mini
    instructions: Process and summarize content.
  store:
    type: function
    handler: StoreResult

edges:
  - from: fetch
    to: process
  - from: process
    to: store
```

Load and run:

```csharp
var workflow = WorkflowBuilder.FromYaml("workflow.yaml")
    .RegisterHandler("FetchContent", FetchContent)
    .RegisterHandler("StoreResult", StoreResult)
    .Build();

await workflow.RunAsync();
```

## Shared State

Share data between executors:

```csharp
var workflow = new WorkflowBuilder()
    .AddExecutor("init", (input, state) =>
    {
        state["counter"] = 0;
        return input;
    })
    .AddExecutor("increment", (input, state) =>
    {
        state["counter"] = (int)state["counter"] + 1;
        return input;
    })
    .AddExecutor("report", (input, state) =>
    {
        return $"Counter: {state["counter"]}";
    })
    .EnableSharedState()
    .Build();
```

## Best Practices

1. **Use checkpointing** for long-running workflows
2. **Set max iterations** on loops to prevent infinite cycles
3. **Implement human-in-the-loop** for critical decisions
4. **Use sub-workflows** to decompose complex logic
5. **Enable streaming** for real-time feedback
6. **Add error handlers** at workflow level
7. **Use shared state sparingly** - prefer passing data through edges
