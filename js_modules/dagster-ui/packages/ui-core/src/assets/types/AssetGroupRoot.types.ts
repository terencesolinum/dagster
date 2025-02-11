// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type AssetGroupMetadataQueryVariables = Types.Exact<{
  selector: Types.AssetGroupSelector;
}>;

export type AssetGroupMetadataQuery = {
  __typename: 'Query';
  assetNodes: Array<{
    __typename: 'AssetNode';
    id: string;
    autoMaterializePolicy: {
      __typename: 'AutoMaterializePolicy';
      policyType: Types.AutoMaterializePolicyType;
    } | null;
    automationPolicySensor: {
      __typename: 'Sensor';
      id: string;
      jobOriginId: string;
      name: string;
      sensorState: {
        __typename: 'InstigationState';
        id: string;
        selectorId: string;
        status: Types.InstigationStatus;
      };
    } | null;
  }>;
};
