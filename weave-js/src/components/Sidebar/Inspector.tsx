import React from 'react';
import styled from 'styled-components';

type InspectorProps = {active: boolean};

export const Inspector: React.FC<InspectorProps> = ({active, children}) => {
  return (
    <Container active={active} data-test="weave-sidebar">
      <Content>{children}</Content>
    </Container>
  );
};

export default Inspector;

const WIDTH_PX = 328;

export const Container = styled.div<{active: boolean}>`
  flex-shrink: 0;
  font-size: 15px;
  overflow: hidden;
  box-shadow: 0px 0px 10px rgba(0, 0, 0, 0.2);

  width: ${p => (p.active ? WIDTH_PX : 0)}px;
  transition: width 0.3s;
`;

export const Content = styled.div`
  width: ${WIDTH_PX}px;
  height: 100%;
`;
