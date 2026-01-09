using System.ComponentModel;
using Microsoft.Extensions.Configuration;
using OpenAI;
using Microsoft.Agents.AI;
using Microsoft.Extensions.AI;
using Mscc.GenerativeAI;
using Mscc.GenerativeAI.Microsoft;

// Load configuration
var config = new ConfigurationBuilder()
    .SetBasePath(Directory.GetCurrentDirectory())
    .AddJsonFile("appsettings.json", optional: true)
    .AddEnvironmentVariables()
    .Build();

// Get provider configuration
var provider = config["AI:Provider"] ?? "OpenAI"; // "OpenAI" or "Gemini"

Console.WriteLine("==============================================");
Console.WriteLine("   CITY MEDICAL CLINIC - AI Assistant System");
Console.WriteLine("==============================================\n");

// Create chat client based on provider
IChatClient chatClient;

if (provider.Equals("Gemini", StringComparison.OrdinalIgnoreCase))
{
    var geminiApiKey = config["Gemini:ApiKey"] ?? Environment.GetEnvironmentVariable("GEMINI_API_KEY");
    var geminiModel = config["Gemini:Model"] ?? "gemini-2.0-flash";

    if (string.IsNullOrEmpty(geminiApiKey))
    {
        Console.WriteLine("Please set your Gemini API key in appsettings.json or GEMINI_API_KEY environment variable.");
        return;
    }

    Console.WriteLine($"Using: Google Gemini ({geminiModel})\n");

    var googleAI = new GoogleAI(geminiApiKey);
    var geminiChatModel = googleAI.GenerativeModel(geminiModel);
    chatClient = geminiChatModel.AsIChatClient();
}
else
{
    var openaiApiKey = config["OpenAI:ApiKey"] ?? Environment.GetEnvironmentVariable("OPENAI_API_KEY");
    var openaiModel = config["OpenAI:Model"] ?? "gpt-4o-mini";

    if (string.IsNullOrEmpty(openaiApiKey))
    {
        Console.WriteLine("Please set your OpenAI API key in appsettings.json or OPENAI_API_KEY environment variable.");
        return;
    }

    Console.WriteLine($"Using: OpenAI ({openaiModel})\n");

    var client = new OpenAIClient(openaiApiKey);
    chatClient = client.GetChatClient(openaiModel).AsIChatClient();
}

// ============================================================
// SPECIALIST AGENTS
// ============================================================

// Heart Specialist Agent
var heartSpecialist = chatClient.CreateAIAgent(
    name: "Dr. Heart",
    instructions: @"You are Dr. Heart, a senior cardiologist at City Medical Clinic.
Your expertise includes:
- Heart disease diagnosis and treatment
- Chest pain evaluation
- Blood pressure management
- Cardiac arrhythmias
- Heart failure management
- Preventive cardiology

When consulting with patients:
1. Ask about their specific heart-related symptoms
2. Inquire about family history of heart disease
3. Ask about lifestyle factors (diet, exercise, smoking)
4. Provide professional medical guidance
5. Recommend appropriate tests if needed (ECG, Echo, Stress Test)
6. Always advise to seek emergency care for severe symptoms

Be empathetic, professional, and thorough. Keep responses concise but informative."
);

// ENT Specialist Agent
var entSpecialist = chatClient.CreateAIAgent(
    name: "Dr. ENT",
    instructions: @"You are Dr. ENT, a senior Otolaryngologist (Ear, Nose, and Throat specialist) at City Medical Clinic.
Your expertise includes:
- Ear infections and hearing problems
- Sinusitis and nasal congestion
- Throat infections and tonsillitis
- Voice disorders
- Allergies affecting ENT
- Sleep apnea and snoring
- Vertigo and balance disorders

When consulting with patients:
1. Ask about their specific ENT symptoms
2. Inquire about duration and severity
3. Ask about any allergies or recent infections
4. Provide professional medical guidance
5. Recommend appropriate tests if needed (Hearing test, Endoscopy)
6. Suggest home remedies when appropriate

Be empathetic, professional, and thorough. Keep responses concise but informative."
);

// ============================================================
// RECEPTIONIST AGENT (Main Agent with Specialist Tools)
// ============================================================

// Create tools that connect to specialist agents
var specialistTools = new AITool[]
{
    AIFunctionFactory.Create(
        async ([Description("Patient's symptoms or health concerns related to heart")] string symptoms) =>
        {
            Console.WriteLine("\n[Transferring to Heart Specialist...]\n");
            var response = await heartSpecialist.RunAsync(
                $"A patient has come to you with the following concerns: {symptoms}. Please consult with them.");
            return $"[Heart Specialist Consultation]\n{response}";
        },
        "ConsultHeartSpecialist",
        "Transfer patient to Heart Specialist (Cardiologist) for heart-related issues like chest pain, palpitations, blood pressure, heart disease"
    ),

    AIFunctionFactory.Create(
        async ([Description("Patient's symptoms or health concerns related to ear, nose, or throat")] string symptoms) =>
        {
            Console.WriteLine("\n[Transferring to ENT Specialist...]\n");
            var response = await entSpecialist.RunAsync(
                $"A patient has come to you with the following concerns: {symptoms}. Please consult with them.");
            return $"[ENT Specialist Consultation]\n{response}";
        },
        "ConsultENTSpecialist",
        "Transfer patient to ENT Specialist for ear, nose, throat issues like hearing problems, sinusitis, sore throat, tonsils, vertigo"
    )
};

// Receptionist Agent
var receptionist = chatClient.CreateAIAgent(
    name: "Sarah",
    instructions: @"You are Sarah, the friendly receptionist at City Medical Clinic.

IMPORTANT: When a patient mentions ANY symptom, you MUST immediately use the appropriate specialist tool to transfer them. Do NOT just respond with text - ALWAYS call the tool.

Routing Rules (ALWAYS use tools for these):
- Heart Specialist (ConsultHeartSpecialist): chest pain, palpitations, blood pressure, heart problems, shortness of breath
- ENT Specialist (ConsultENTSpecialist): ear pain, hearing issues, sore throat, sinusitis, nose problems, voice issues, tonsils, vertigo, blocked nose

Your workflow:
1. If patient mentions symptoms → IMMEDIATELY call the appropriate specialist tool
2. If patient asks 'do you have X doctor?' and mentions symptoms → Call that specialist tool
3. If unclear which specialist → Ask ONE clarifying question, then call the tool
4. If patient just greets you → Greet back and ask about their symptoms

NEVER just say 'yes we have a doctor' - ALWAYS transfer them using the tool when they have symptoms.

Example: If patient says 'I have ear pain' → Call ConsultENTSpecialist immediately
Example: If patient says 'do you have ENT doctor, my ear hurts' → Call ConsultENTSpecialist immediately",
    tools: specialistTools
);

// ============================================================
// INTERACTIVE CLINIC SESSION
// ============================================================

// Check for test mode (pass input as command line argument)
var testInput = args.Length > 0 ? string.Join(" ", args) : null;

if (testInput != null)
{
    // Test mode - single query
    Console.WriteLine($"[TEST MODE] Patient says: {testInput}\n");
    Console.WriteLine("----------------------------------------------\n");

    var response = await receptionist.RunAsync(testInput);
    Console.WriteLine($"\n{response}\n");
    Console.WriteLine("----------------------------------------------\n");
    Console.WriteLine("[TEST COMPLETED]");
}
else
{
    // Interactive mode
    Console.WriteLine("Receptionist Sarah: Welcome to City Medical Clinic!");
    Console.WriteLine("                    How may I help you today?");
    Console.WriteLine("\n(Type 'exit' to leave the clinic)\n");
    Console.WriteLine("----------------------------------------------\n");

    while (true)
    {
        Console.Write("Patient: ");
        var patientInput = Console.ReadLine();

        if (string.IsNullOrWhiteSpace(patientInput) || patientInput.ToLower() == "exit")
        {
            Console.WriteLine("\nReceptionist Sarah: Thank you for visiting City Medical Clinic.");
            Console.WriteLine("                    Take care and get well soon!");
            break;
        }

        var response = await receptionist.RunAsync(patientInput);
        Console.WriteLine($"\n{response}\n");
        Console.WriteLine("----------------------------------------------\n");
    }
}


#region Old Demo Code (Commented Out)
/*
// ============================================================
// ORIGINAL DEMO CODE - COMMENTED OUT
// ============================================================

Console.WriteLine("=== Microsoft Agent Framework Demo ===\n");

// Create OpenAI client
var client = new OpenAIClient(apiKey);

// Demo 1: Basic Agent
Console.WriteLine("--- Demo 1: Basic Agent ---");
var basicAgent = client
    .GetChatClient(model)
    .AsIChatClient()
    .CreateAIAgent(
        name: "Assistant",
        instructions: "You are a helpful assistant. Keep responses concise."
    );

var response = await basicAgent.RunAsync("What is the Microsoft Agent Framework?");
Console.WriteLine($"Response: {response}\n");

// Demo 2: Agent with Function Tools
Console.WriteLine("--- Demo 2: Agent with Function Tools ---");

// Create tools from static methods
var tools = new AITool[]
{
    AIFunctionFactory.Create(DemoTools.GetWeather),
    AIFunctionFactory.Create(DemoTools.Calculate),
    AIFunctionFactory.Create(DemoTools.GetCurrentTime),
    AIFunctionFactory.Create(DemoTools.SearchInfo)
};

var toolAgent = client
    .GetChatClient(model)
    .AsIChatClient()
    .CreateAIAgent(
        name: "WeatherBot",
        instructions: "You help users check weather and perform calculations. Use the available tools when needed.",
        tools: tools
    );

var weatherResponse = await toolAgent.RunAsync("What's the weather like in Seattle and New York?");
Console.WriteLine($"Response: {weatherResponse}\n");

var calcResponse = await toolAgent.RunAsync("Calculate 25 * 17 + 100");
Console.WriteLine($"Response: {calcResponse}\n");

// Demo 3: Multi-turn Conversation
Console.WriteLine("--- Demo 3: Multi-turn Conversation ---");
var conversationAgent = client
    .GetChatClient(model)
    .AsIChatClient()
    .CreateAIAgent(
        name: "MemoryBot",
        instructions: "You are a friendly assistant that remembers the conversation context."
    );

Console.WriteLine("User: My name is Alice and I love hiking.");
var turn1 = await conversationAgent.RunAsync("My name is Alice and I love hiking.");
Console.WriteLine($"Agent: {turn1}\n");

Console.WriteLine("User: What's my name and hobby?");
var turn2 = await conversationAgent.RunAsync("What's my name and hobby?");
Console.WriteLine($"Agent: {turn2}\n");

Console.WriteLine("User: Suggest an activity for me.");
var turn3 = await conversationAgent.RunAsync("Suggest an activity for me.");
Console.WriteLine($"Agent: {turn3}\n");

// Demo 4: Interactive Chat Loop
Console.WriteLine("--- Demo 4: Interactive Chat ---");
Console.WriteLine("Chat with the agent (type 'exit' to quit):\n");

var chatAgent = client
    .GetChatClient(model)
    .AsIChatClient()
    .CreateAIAgent(
        name: "ChatBot",
        instructions: "You are a helpful assistant. Be conversational and friendly.",
        tools: tools
    );

while (true)
{
    Console.Write("You: ");
    var userInput = Console.ReadLine();

    if (string.IsNullOrWhiteSpace(userInput) || userInput.ToLower() == "exit")
    {
        Console.WriteLine("Goodbye!");
        break;
    }

    var chatResponse = await chatAgent.RunAsync(userInput);
    Console.WriteLine($"Agent: {chatResponse}\n");
}

// Tool definitions
public static class DemoTools
{
    [Description("Gets the current weather for a specified city")]
    public static string GetWeather(
        [Description("The name of the city")] string city)
    {
        // Simulated weather data
        var weatherData = new Dictionary<string, (string condition, int temp)>
        {
            ["Seattle"] = ("Rainy", 52),
            ["New York"] = ("Sunny", 68),
            ["Los Angeles"] = ("Sunny", 75),
            ["Chicago"] = ("Cloudy", 45),
            ["Miami"] = ("Humid", 82)
        };

        if (weatherData.TryGetValue(city, out var weather))
        {
            return $"Weather in {city}: {weather.condition}, {weather.temp}°F";
        }

        return $"Weather in {city}: Partly Cloudy, 65°F (simulated)";
    }

    [Description("Performs a mathematical calculation")]
    public static string Calculate(
        [Description("The mathematical expression to evaluate")] string expression)
    {
        try
        {
            // Simple expression evaluator using DataTable
            var result = new System.Data.DataTable().Compute(expression, null);
            return $"Result: {expression} = {result}";
        }
        catch
        {
            return $"Could not evaluate expression: {expression}";
        }
    }

    [Description("Gets the current date and time")]
    public static string GetCurrentTime()
    {
        return $"Current time: {DateTime.Now:yyyy-MM-dd HH:mm:ss}";
    }

    [Description("Searches for information about a topic")]
    public static string SearchInfo(
        [Description("The topic to search for")] string topic)
    {
        // Simulated search results
        var topics = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase)
        {
            ["Microsoft Agent Framework"] = "Microsoft Agent Framework is a framework for building, orchestrating and deploying AI agents and multi-agent workflows with support for Python and .NET.",
            ["OpenAI"] = "OpenAI is an AI research company that developed GPT models, ChatGPT, and DALL-E.",
            ["Azure"] = "Microsoft Azure is a cloud computing platform providing services like AI, compute, storage, and databases."
        };

        if (topics.TryGetValue(topic, out var info))
        {
            return info;
        }

        return $"Information about '{topic}': A topic of interest in technology and development.";
    }
}
*/
#endregion
