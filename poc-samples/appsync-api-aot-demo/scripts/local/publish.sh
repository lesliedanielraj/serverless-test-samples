SCRIPT_ROOT=$(dirname $(realpath "$0"))
echo -e '\nRunning publish.sh\n'

find . -name "dist" -exec rm -rf {} +
cd "$SCRIPT_ROOT"/../../src/AppSyncApiAot.Core
dotnet lambda package -farch arm64 -ucfb true -o "$SCRIPT_ROOT"/../../dist/release/publish/AppSyncApiAot.GetUserDetail.zip
#dotnet lambda package -farch x86_64 -ucfb true -o "$SCRIPT_ROOT"/../../dist/release/publish/AppSyncApiAot.Core
#dotnet publish -c Release -r linux-x64 -p:Version=2.0.0.0 --no-self-contained -o $SCRIPT_ROOT/../../dist/release/publish/AppSyncApiAot.Api
#dotnet publish  -o $SCRIPT_ROOT/../../dist/release/publish/AppSyncApiAot.Api --configuration "Release" /p:GenerateRuntimeConfigurationFiles=true --runtime linux-arm64 --self-contained True  /p:StripSymbols=true
echo -e '\nListing published files\n'
cd "$SCRIPT_ROOT"/../../dist/release/publish/AppSyncApiAot.GetUserDetail
ls -la
