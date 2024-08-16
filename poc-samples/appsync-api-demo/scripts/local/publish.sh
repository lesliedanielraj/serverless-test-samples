SCRIPT_ROOT=$(dirname $(realpath "$0"))
echo -e '\nRunning publish.sh\n'

find . -name "dist" -exec rm -rf {} +
cd $SCRIPT_ROOT/../../src/AppSyncApiDemo.Api
dotnet publish -c Release -r linux-x64 -p:Version=2.0.0.0 --no-self-contained -o $SCRIPT_ROOT/../../dist/release/publish/AppSyncApiDemo.Api

echo -e '\nListing published files\n'
cd $SCRIPT_ROOT/../../dist/release/publish/AppSyncApiDemo.Api
ls -la
