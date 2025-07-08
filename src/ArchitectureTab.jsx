import React, { useEffect, useState } from 'react';
import mermaid from 'mermaid';
import { motion } from 'framer-motion';
import { TransformWrapper, TransformComponent } from 'react-zoom-pan-pinch';
import { ZoomIn, ZoomOut, Maximize } from 'lucide-react';

const mermaidChart = `
graph TD
    subgraph "Start"
        UserQueryInput[/"User Query"/]:::userInput
    end

    UserQueryInput --> TriageAgent["🤖 Triage Agent"];

    subgraph "Decision Point 1: Triage"
        TriageAgent --> TriageDecision{Is query valid & complex?};
        TriageDecision -- "Yes, Engage/Direct<br/>(Complex/Specific Query)" --> PlanningAgent["🤖 Planning Agent"];
        TriageDecision -- "No, Clarify" --> EndClarify["END<br/>(Request for more detail)"];
        TriageDecision -- "No, Reject" --> EndReject["END<br/>(Out of scope)"];
    end

    subgraph "Decision Point 2: Planning"
        PlanningAgent --> PlanningDecision{Develop a strategy};
        PlanningDecision -- "Research Plan" --> ResearchOrchestrator["🔄 Research Orchestrator"];
        PlanningDecision -- "Direct Retrieval" --> SynthesisAgent["📝 Synthesis Agent"];
        PlanningDecision -- "Simple Answer" --> EndSimple["END<br/>(Provide direct answer)"];
    end

    subgraph "Step 3: Research & Validation"
        ResearchOrchestrator --> ParallelExecution["Parallel Sub-Query Execution"];
        
        subgraph "Internal Fallback Chain"
            direction LR
            ParallelExecution --> CacheCheck{Cache Check};
            CacheCheck -- "Miss" --> VectorSearch[Vector Search];
            VectorSearch --> GraphSearch[Graph Search];
            GraphSearch --> KeywordSearch[Keyword Search];
            KeywordSearch --> WebSearch[Web Search];
            WebSearch --> CollectResults[Collect Results];
            CacheCheck -- "Hit" --> CollectResults;
        end

        CollectResults --> ValidationAgent["🔬 Validation Agent"];
    end

    subgraph "Decision Point 4: Validation"
        ValidationAgent --> ValidationDecision{"Assess Research Quality<br/>& Detect Math"};
        ValidationDecision -- "🔥 Math Detected<br/>(Absolute Priority)" --> CalculationExecutor["🧮 Calculation Executor"];
        ValidationDecision -- "📝 Research Insufficient" --> PlaceholderHandler["📝 Placeholder Handler"];
        ValidationDecision -- "✅ Research Sufficient" --> SynthesisAgent;
    end

    subgraph "Step 5: Augmentation (Conditional)"
        style CalculationExecutor fill:#4a044e,stroke:#a21caf,color:white
        style PlaceholderHandler fill:#7f1d1d,stroke:#ef4444,color:white
        CalculationExecutor -- "Append Calculation Results" --> SynthesisAgent;
        PlaceholderHandler -- "Generate Partial Answer" --> SynthesisAgent;
    end

    subgraph "Step 6: Finalization"
        SynthesisAgent --> FinalAnswer["Assemble Final Answer<br/>w/ Citations & Scoring"];
        FinalAnswer --> MemoryAgent["💾 Memory Agent"];
        MemoryAgent --> EndSuccess["END<br/>(Store conversation & complete)"];
    end

    classDef default fill:#111827,stroke:#374151,stroke-width:2px,color:white;
    classDef userInput fill:#047857,stroke:#059669,stroke-width:3px,color:white;
    class TriageDecision,PlanningDecision,ValidationDecision fill:#4f46e5,stroke:#818cf8,color:white;
    class EndClarify,EndReject,EndSimple,EndSuccess fill:#166534,stroke:#22c55e,color:white;
`;

const ArchitectureTab = () => {
  const [svg, setSvg] = useState('');

  useEffect(() => {
    mermaid.initialize({
      startOnLoad: false,
      theme: 'dark',
      securityLevel: 'loose',
      themeVariables: {
        background: 'transparent', // Use transparent for wrapper
        primaryColor: '#1f2937',
        primaryTextColor: '#d1d5db',
        primaryBorderColor: '#4b5563',
        lineColor: '#6b7280',
        secondaryColor: '#374151',
        tertiaryColor: '#1f2937',
        nodeBorder: '#818cf8',
        mainBkg: '#1e40af',
        textColor: '#ffffff',
        edgeLabelBackground: '#1f2937',
        clusterBkg: 'rgba(31, 41, 55, 0.5)',
        clusterBorder: '#4b5563',
        successBkg: '#166534',
        successBorder: '#22c55e',
        tertiaryBorderColor: '#059669',
        tertiaryBkg: '#047857',
      },
      fontFamily: 'sans-serif',
    });

    const renderMermaid = async () => {
        try {
            const { svg } = await mermaid.render('mermaid-svg', mermaidChart);
            setSvg(svg);
        } catch (error) {
            console.error('Mermaid rendering failed:', error);
        }
    };
    renderMermaid();
  }, []);

  const Controls = ({ zoomIn, zoomOut, resetTransform }) => (
    <div className="absolute top-4 right-4 z-10 flex gap-2">
      <button onClick={() => zoomIn()} className="p-2 bg-gray-700/80 rounded-md hover:bg-gray-600 transition-colors">
        <ZoomIn size={20} />
      </button>
      <button onClick={() => zoomOut()} className="p-2 bg-gray-700/80 rounded-md hover:bg-gray-600 transition-colors">
        <ZoomOut size={20} />
      </button>
      <button onClick={() => resetTransform()} className="p-2 bg-gray-700/80 rounded-md hover:bg-gray-600 transition-colors">
        <Maximize size={20} />
      </button>
    </div>
  );

  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -15 }}
      transition={{ duration: 0.25 }}
      className="h-full w-full relative"
    >
      <TransformWrapper
        minScale={0.2}
        maxScale={4}
        initialScale={1}
        initialPositionX={0}
        initialPositionY={0}
        centerZoomedOut={true}
      >
        {({ zoomIn, zoomOut, resetTransform, ...rest }) => (
          <React.Fragment>
            <Controls zoomIn={zoomIn} zoomOut={zoomOut} resetTransform={resetTransform} />
            <TransformComponent
              wrapperStyle={{ width: '100%', height: '100%' }}
              contentStyle={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', width: '100%' }}
            >
              {svg ? (
                <div dangerouslySetInnerHTML={{ __html: svg }} />
              ) : (
                <p>Loading Diagram...</p>
              )}
            </TransformComponent>
          </React.Fragment>
        )}
      </TransformWrapper>
    </motion.div>
  );
};

export default ArchitectureTab; 