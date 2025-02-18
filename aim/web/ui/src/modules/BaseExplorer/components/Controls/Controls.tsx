import React from 'react';
import { omit } from 'lodash-es';

import { ControlsConfigs } from 'modules/core/engine/visualizations/controls';

import ErrorBoundary from 'components/ErrorBoundary/ErrorBoundary';

import { IControlsProps } from '../../types';

import './Controls.scss';

function Controls(props: IControlsProps) {
  const { controls = [] } = props.engine.visualizations[
    props.visualizationName
  ] as Record<'controls', ControlsConfigs & { reset: () => void }>;

  const Components = React.useMemo(
    () =>
      Object.entries(omit(controls, ['reset'])).map(([key, Control]) => {
        // @ts-ignore
        const Component = Control.component;

        return (
          <div key={key} className='Control'>
            <Component {...props} />
          </div>
        );
      }),
    [controls, props],
  );

  return (
    <ErrorBoundary>
      <div className='BaseControls'>
        <div className='BaseControls__container ScrollBar__hidden'>
          {Components}
        </div>
      </div>
    </ErrorBoundary>
  );
}

Controls.diplayName = 'Controls';

export default React.memo<IControlsProps>(Controls);
