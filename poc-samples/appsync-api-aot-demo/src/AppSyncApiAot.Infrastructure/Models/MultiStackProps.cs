using Amazon.CDK;

namespace AppSyncApiAot.Infrastructure.Models;

public class MultiStackProps : StackProps
{
    // public Table PreferenceTable { get; set; }
    public string AppSyncDomain { get; set; }
    public string AppSyncGatewayPath { get; set; }
    public string VpcCidr { get; set; }
    public int NumberOfAZs { get; set; }
}