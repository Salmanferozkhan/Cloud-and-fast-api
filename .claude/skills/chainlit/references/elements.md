# UI Elements Reference

## Table of Contents
- [Overview](#overview)
- [Display Modes](#display-modes)
- [Text Element](#text-element)
- [Image Element](#image-element)
- [File Element](#file-element)
- [PDF Element](#pdf-element)
- [Audio Element](#audio-element)
- [Video Element](#video-element)
- [Plotly Element](#plotly-element)
- [Dataframe Element](#dataframe-element)
- [TaskList Element](#tasklist-element)

## Overview

Elements are rich UI components attached to messages. They display content like text, images, files, charts, and more.

## Display Modes

| Mode | Description |
|------|-------------|
| `inline` | Display within message |
| `side` | Display in side panel |
| `page` | Display in full page |

## Text Element

Display formatted text content:

```python
import chainlit as cl

@cl.on_message
async def on_message(message: cl.Message):
    # Basic text
    text = cl.Text(
        name="response.txt",
        content="This is the detailed response...",
        display="inline"
    )

    await cl.Message(
        content="Here's the analysis:",
        elements=[text]
    ).send()
```

### Code with Syntax Highlighting

```python
code = cl.Text(
    name="example.py",
    content='''def hello():
    print("Hello, World!")
''',
    language="python",
    display="side"
)

await cl.Message(
    content="Here's the code:",
    elements=[code]
).send()
```

### From File

```python
text = cl.Text(
    name="document.txt",
    path="./documents/report.txt",
    display="page"
)
```

## Image Element

Display images:

```python
@cl.on_message
async def on_message(message: cl.Message):
    # From file path
    image = cl.Image(
        name="chart.png",
        path="./output/chart.png",
        display="inline"
    )

    await cl.Message(
        content="Here's the chart:",
        elements=[image]
    ).send()
```

### From URL

```python
image = cl.Image(
    name="logo",
    url="https://example.com/logo.png",
    display="inline"
)
```

### From Bytes

```python
import base64

# Generate image bytes
image_bytes = generate_image()

image = cl.Image(
    name="generated.png",
    content=image_bytes,
    display="inline"
)
```

## File Element

Provide downloadable files:

```python
@cl.on_message
async def on_message(message: cl.Message):
    # Create file for download
    file = cl.File(
        name="report.pdf",
        path="./output/report.pdf",
        display="inline"
    )

    await cl.Message(
        content="Download your report:",
        elements=[file]
    ).send()
```

### Multiple Files

```python
files = [
    cl.File(name="data.csv", path="./data.csv"),
    cl.File(name="summary.txt", path="./summary.txt"),
]

await cl.Message(
    content="Here are your files:",
    elements=files
).send()
```

## PDF Element

Display PDF documents:

```python
@cl.on_message
async def on_message(message: cl.Message):
    pdf = cl.Pdf(
        name="document.pdf",
        path="./documents/paper.pdf",
        display="side"
    )

    await cl.Message(
        content="Here's the PDF:",
        elements=[pdf]
    ).send()
```

## Audio Element

Play audio content:

```python
@cl.on_message
async def on_message(message: cl.Message):
    audio = cl.Audio(
        name="speech.mp3",
        path="./output/speech.mp3",
        display="inline"
    )

    await cl.Message(
        content="Listen to the audio:",
        elements=[audio]
    ).send()
```

### From URL

```python
audio = cl.Audio(
    name="podcast",
    url="https://example.com/episode.mp3",
    display="inline"
)
```

## Video Element

Display video content:

```python
@cl.on_message
async def on_message(message: cl.Message):
    video = cl.Video(
        name="tutorial.mp4",
        path="./videos/tutorial.mp4",
        display="inline"
    )

    await cl.Message(
        content="Watch the tutorial:",
        elements=[video]
    ).send()
```

## Plotly Element

Interactive Plotly charts:

```python
import plotly.graph_objects as go

@cl.on_message
async def on_message(message: cl.Message):
    # Create Plotly figure
    fig = go.Figure(
        data=[go.Bar(x=["A", "B", "C"], y=[1, 3, 2])],
        layout=go.Layout(title="Sample Chart")
    )

    chart = cl.Plotly(
        name="chart",
        figure=fig,
        display="inline"
    )

    await cl.Message(
        content="Here's the chart:",
        elements=[chart]
    ).send()
```

## Dataframe Element

Display tabular data:

```python
import pandas as pd

@cl.on_message
async def on_message(message: cl.Message):
    # Create dataframe
    df = pd.DataFrame({
        "Name": ["Alice", "Bob", "Charlie"],
        "Score": [95, 87, 92]
    })

    table = cl.Dataframe(
        name="results",
        data=df,
        display="inline"
    )

    await cl.Message(
        content="Here are the results:",
        elements=[table]
    ).send()
```

## TaskList Element

Display progress on tasks:

```python
@cl.on_chat_start
async def start():
    # Create task list
    task_list = cl.TaskList()
    task_list.status = "Running"

    # Add tasks
    task1 = cl.Task(title="Loading data", status=cl.TaskStatus.RUNNING)
    task2 = cl.Task(title="Processing", status=cl.TaskStatus.READY)
    task3 = cl.Task(title="Generating output", status=cl.TaskStatus.READY)

    await task_list.add_task(task1)
    await task_list.add_task(task2)
    await task_list.add_task(task3)

    await task_list.send()

    # Update tasks as they complete
    task1.status = cl.TaskStatus.DONE
    await task_list.update()

    task2.status = cl.TaskStatus.RUNNING
    await task_list.update()

    # ... continue updating
```

## Complete Example

Message with multiple elements:

```python
import chainlit as cl
import plotly.express as px
import pandas as pd

@cl.on_message
async def on_message(message: cl.Message):
    # Create various elements
    df = pd.DataFrame({"x": [1, 2, 3], "y": [4, 5, 6]})

    elements = [
        cl.Text(
            name="analysis.md",
            content="## Analysis Results\n\nThe data shows...",
            display="side"
        ),
        cl.Plotly(
            name="chart",
            figure=px.line(df, x="x", y="y", title="Trend"),
            display="inline"
        ),
        cl.Dataframe(
            name="data",
            data=df,
            display="inline"
        ),
    ]

    await cl.Message(
        content="Here's your complete analysis:",
        elements=elements
    ).send()
```
