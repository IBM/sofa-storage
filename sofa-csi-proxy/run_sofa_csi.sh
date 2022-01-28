#!/bin/bash

export SOFA_CSI_ENDPOINT='unix:///csi/csi.sock'
export SOFA_CSI_TARGET='unix:///csi/sofacsi.sock'
export SOFA_ENDPOINT=''

if [ -f /etc/sofa/sofacsi.env ]; then
    echo "SOFA CSI: Setting local env vars"
    source /etc/sofa/sofacsi.env
fi

/sofa-csi-plugin/sofa-storage-csi -v=5 --nodeid=$NODE_ID --endpoint=$SOFA_CSI_ENDPOINT --csitarget=$SOFA_CSI_TARGET --sofa=$SOFA_ENDPOINT

