import {
  DataGridProProps,
  GridApiPro,
  GridColDef,
  GridRowHeightParams,
} from '@mui/x-data-grid-pro';
import _ from 'lodash';
import React, {useEffect, useMemo, useState} from 'react';

import {useWeaveContext} from '../../../../../../context';
import {isWeaveObjectRef, parseRef} from '../../../../../../react';
import {parseRefMaybe} from '../../../Browse2/SmallRef';
import {StyledDataGrid} from '../../StyledDataGrid';
import {isRef} from '../common/util';
import {useWFHooks} from '../wfReactInterface/context';
import {processGenericData} from './CallDetails';
import {ObjectViewerGroupingCell} from './ObjectViewerGroupingCell';
import {mapObject, traverse, TraverseContext, traversed} from './traverse';
import {ValueView} from './ValueView';

type Data = Record<string, any>;

type ObjectViewerProps = {
  apiRef: React.MutableRefObject<GridApiPro>;
  data: Data;
  isExpanded: boolean;
};

// Traverse the data and find all ref URIs.
const getRefs = (data: Data): string[] => {
  const refs = new Set<string>();
  traverse(data, (context: TraverseContext) => {
    if (isRef(context.value) && context.path.tail() !== '_ref') {
      const parsedRef = parseRef(context.value);
      if (isWeaveObjectRef(parsedRef)) {
        if (parsedRef.weaveKind === 'object') {
          refs.add(context.value);
        }
      }
    }
  });
  return Array.from(refs);
};

type RefValues = Record<string, any>; // ref URI to value

export const ObjectViewer = ({apiRef, data, isExpanded}: ObjectViewerProps) => {
  const weave = useWeaveContext();
  const {useRefsData} = useWFHooks();
  const {client} = weave;
  const [resolvedData, setResolvedData] = useState<Data>(data);
  const refs = useMemo(() => getRefs(data), [data]);
  const refsData = useRefsData(refs);

  useEffect(() => {
    const resolvedRefData = refsData.result;

    const refValues: RefValues = {};
    for (const [r, v] of _.zip(refs, resolvedRefData)) {
      if (!r || !v) {
        // Shouldn't be possible
        continue;
      }
      // // Hack: make this general. Don't expand ops
      // if (v.weave_type?.type === 'OpDef') {
      //   refValues[r] = r;
      //   continue;
      // }
      let val = r;
      if (v == null) {
        console.error('Error resolving ref', r);
      } else {
        val = v;
        if (typeof val === 'object' && val !== null) {
          val = {
            ...processGenericData(v),
            _ref: r,
          };
        }
      }
      refValues[r] = val;
    }
    const resolved = mapObject(data, context => {
      if (isRef(context.value) && refValues[context.value]) {
        return refValues[context.value];
      }
      return context.value;
    });
    setResolvedData(resolved);
  }, [data, client, refsData.result, refs]);

  const rows = useMemo(() => {
    const contexts = traversed(
      resolvedData,
      c =>
        c.depth !== 0 && !c.path.endsWith('_ref') && !c.path.endsWith('_type'),
      c => {
        if (c.valueType === 'array') return 'skip';
        return undefined;
      }
    );
    return contexts.map((c, id) => ({id, ...c}));
  }, [resolvedData]);

  const columns: GridColDef[] = [
    {
      field: 'value',
      headerName: 'Value',
      flex: 1,
      sortable: false,
      renderCell: ({row}) => {
        return <ValueView data={row} isExpanded={isExpanded} />;
      },
    },
  ];

  const groupingColDef: DataGridProProps['groupingColDef'] = useMemo(
    () => ({
      headerName: 'Path',
      hideDescendantCount: true,
      renderCell: params => <ObjectViewerGroupingCell {...params} />,
    }),
    []
  );

  return (
    <div style={{overflow: 'hidden'}}>
      <StyledDataGrid
        apiRef={apiRef}
        treeData
        getTreeDataPath={row => row.path.toStringArray()}
        rows={rows}
        columns={columns}
        defaultGroupingExpansionDepth={isExpanded ? -1 : 0}
        columnHeaderHeight={38}
        getRowHeight={(params: GridRowHeightParams) => {
          if (
            (params.model.valueType === 'string' &&
              isRef(params.model.value) &&
              (parseRefMaybe(params.model.value) as any).weaveKind ===
                'table') ||
            params.model.valueType === 'array'
          ) {
            return 'auto';
          }
          return 38;
        }}
        hideFooter
        rowSelection={false}
        disableColumnMenu={true}
        groupingColDef={groupingColDef}
        sx={{
          '& .MuiDataGrid-row:hover': {
            backgroundColor: 'inherit',
          },
          '& > div > div > div > div > .MuiDataGrid-row > .MuiDataGrid-cell': {
            paddingRight: '0px',
          },
        }}
      />
    </div>
  );
};
