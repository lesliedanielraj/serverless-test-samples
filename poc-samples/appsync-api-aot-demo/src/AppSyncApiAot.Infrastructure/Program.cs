using Amazon.CDK;
using AppSyncApiAot.Infrastructure.Models;
using AppSyncApiAot.Infrastructure.Stacks;

namespace AppSyncApiAot.Infrastructure
{
    public sealed class Program
    {
        public static void Main(string[] args)
        {
            var app = new App();

            var appSyncStack = new AppSyncAotStack(app, "AppSyncAotStack");
            _ = new ApiGatewayAotStack(app, "ApiGatewayAotStack", new MultiStackProps
            {
                AppSyncDomain = appSyncStack.AppSyncDomain,
                AppSyncGatewayPath = "graphql",
                VpcCidr = "10.0.0.0/16",
                NumberOfAZs = 2
            });

            app.Synth();
        }
    }
}