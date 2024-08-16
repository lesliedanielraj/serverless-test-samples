##usage: .\deploy.sh yourprefix
#!/bin/bash
prefix=${1:-""}

./publish.sh
cd  ../../
echo -e '\nRunning cdk deploy for AppSyncStack\n'
cdk deploy "AppSyncStack" -c prefix="$prefix" --require-approval never
cdk deploy "ApiGatewayStack" -c prefix="$prefix" --require-approval never
