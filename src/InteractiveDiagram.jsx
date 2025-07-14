import React from 'react';
import { TransformWrapper, TransformComponent } from 'react-zoom-pan-pinch';
import DiagramImage from './assets/architectural-diagram.jpg';

const InteractiveDiagram = () => {
  return (
    <div style={{ position: 'relative', width: '100%', height: '100%', overflow: 'hidden' }}>
      <TransformWrapper
        initialScale={1}
        minScale={0.5}
        maxScale={8}
      >
        <TransformComponent
          wrapperStyle={{ width: "100%", height: "100%" }}
          contentStyle={{
            width: "100%",
            height: "100%",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <img
            src={DiagramImage}
            alt="Flow Diagram"
            style={{ maxWidth: '100%', maxHeight: '100%', objectFit: 'contain' }}
          />
        </TransformComponent>
      </TransformWrapper>
    </div>
  );
};

export default InteractiveDiagram; 