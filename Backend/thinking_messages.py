
"""
This file contains a library of predefined, human-like "thinking" messages
for each agent in the workflow. These messages are used when an agent
does not produce its own explicit reasoning output.
"""

THINKING_MESSAGES = {
    "TriageAgent": [
        "Alright, let's see what we have here. What is the user really asking?",
        "Hmm, is this a simple question I can answer directly, or does it need more in-depth research?",
        "Okay, I know how to handle this. I'll route it to the right specialist."
    ],
    "ContextualAnsweringAgent": [
        "Have we talked about this before? Let me check our recent conversation.",
        "I think I have enough context to answer this directly. Let me put together a response.",
        "Let me see if I can answer this without a full-blown research."
    ],
    "PlanningAgent": [
        "This is a complex one. I need to break it down into smaller pieces.",
        "Okay, let's create a plan. First, I'll look into X, then Y, and finally Z.",
        "The plan looks solid. Time to start the research."
    ],
    "HydeAgent": [
        "To get the best results, I'll imagine what a perfect answer might look like.",
        "I'll create a hypothetical document to guide my search. This should help me find the most relevant information.",
        "This hypothetical answer should act as a good signpost for my research."
    ],
    "ResearchOrchestrator": [
        "Time to dig in. I'll search all my sources at once to be efficient.",
        "I'm checking the vector database, the knowledge graph, and the web simultaneously.",
        "Okay, the results are coming in. Let's see what I've found."
    ],
    "EnhancedSynthesisAgent": [
        "Now, let's piece all this information together.",
        "I need to connect the dots between these different findings and form a single, coherent answer.",
        "I'll write out the final answer now, making sure to cite my sources."
    ],
    "MemoryAgent": [
        "This was a good conversation. I'll save the important parts to my memory.",
        "Let me make a note of this so I don't forget it for next time.",
        "All done. This interaction is now part of my long-term memory."
    ],
    "ErrorHandler": [
        "Oops, something went wrong. Let me take a step back and see what happened.",
        "Okay, that didn't work. Let's try a different approach.",
        "I'll try to recover from this error and get us back on track."
    ]
}
