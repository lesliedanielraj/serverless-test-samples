using Amazon.CDK;
using AppSyncApiDemo.Infrastructure.Models;
using AppSyncApiDemo.Infrastructure.Stacks;

namespace AppSyncApiDemo.Infrastructure
{
    public sealed class Program
    {
        public static void Main(string[] args)
        {
            var app = new App();

            var appSyncStack = new AppSyncStack(app, "AppSyncStack");
            _ = new ApiGatewayStack(app, "ApiGatewayStack", new MultiStackProps
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