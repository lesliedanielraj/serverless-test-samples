using System.Collections.Generic;
using System.Linq;
using Amazon.CDK;
using Amazon.CDK.AWS.APIGateway;
using Amazon.CDK.AWS.EC2;
using Amazon.CDK.AWS.ElasticLoadBalancingV2;
using Amazon.CDK.AWS.ElasticLoadBalancingV2.Targets;
using Amazon.CDK.AWS.Route53;
using Amazon.CDK.AWS.Route53.Targets;
using Amazon.CDK.CustomResources;
using AppSyncApiAot.Infrastructure.Models;
using Constructs;

namespace AppSyncApiAot.Infrastructure.Stacks;

public sealed class ApiGatewayAotStack : Stack
{
    internal ApiGatewayAotStack(Construct scope, string id, MultiStackProps props = null) : base(scope, id, props)
    {
        //Create VPC
        var vpc = new Vpc(this, $"{id}-AppSyncApiGatewayVpc", new VpcProps
        {
            IpAddresses = IpAddresses.Cidr(props.VpcCidr),
            MaxAzs = props.NumberOfAZs,
            VpcName = $"{id}-AppSyncApiGatewayVpc",
            SubnetConfiguration =
            [
                new SubnetConfiguration
                {
                    Name = $"{id}-gs-router-isolated",
                    SubnetType = SubnetType.PRIVATE_ISOLATED,
                    CidrMask = 22
                }
            ]
        });

        //Create Appsync Vpc Endpoint
        var vpcEndpoint = vpc.AddInterfaceEndpoint($"{id}-AppSyncVpcEndpoint", new InterfaceVpcEndpointProps
        {
            Service = new InterfaceVpcEndpointService(
                name: "com.amazonaws.us-east-1.appsync-api",
                port: 443d
            ),
            PrivateDnsEnabled = false,
            Open = true,
            Subnets = new SubnetSelection
            {
                SubnetType = SubnetType.PRIVATE_ISOLATED
            }
        });

        //Create NetworkLoadBalancer Targeting Vpc Endpoint
        var nlb = CreateNetworkLoadBalancerTargetingVpcEndpoint(vpc, vpcEndpoint, props.NumberOfAZs, id);

        //Create AppSync Private Hosted Zone
        var hostedZone = CreateAppSyncPrivateHostedZone(vpc, nlb, id);

        //Create Rest Api with AppSync Origin
        var restApi = CreateRestApiWithAppSyncOrigin(
            props.AppSyncDomain,
            props.AppSyncGatewayPath,
            nlb,
            id
        );

        _ = new CfnOutput(this, "RestApiUrl", new CfnOutputProps
        {
            Value = restApi.Url,
            Description = "REST API Url"
        });

        _ = new CfnOutput(this, "HostedZone", new CfnOutputProps
        {
            Value = hostedZone.ZoneName,
            Description = "Hosted Zone"
        });
    }

    private NetworkLoadBalancer CreateNetworkLoadBalancerTargetingVpcEndpoint(Vpc vpc,
        InterfaceVpcEndpoint vpcEndpoint,
        int noOfAZs, string id)
    {
        var ipAddresses = GetIpAddressesForVpcEndpoint(vpcEndpoint, noOfAZs, id);

        var nlb = new NetworkLoadBalancer(this, $"{id}-NLB", new NetworkLoadBalancerProps
        {
            Vpc = vpc,
            InternetFacing = false,
            LoadBalancerName = $"{id}-Nlb",
            VpcSubnets = new SubnetSelection
            {
                SubnetType = SubnetType.PRIVATE_ISOLATED
            }
        });

        var nlbListener = nlb.AddListener($"{id}-NLBListener", new NetworkListenerProps
        {
            Port = 443
        });

        nlbListener.AddTargets($"{id}-NLBTargetGroup", new AddNetworkTargetsProps
        {
            Port = 443,
            Targets = ipAddresses.Select(ip => new IpTarget(ip)).ToArray(),
            HealthCheck = new HealthCheck
            {
                Port = "443",
                Protocol = Amazon.CDK.AWS.ElasticLoadBalancingV2.Protocol.TCP
            }
        });

        return nlb;
    }

    private PrivateHostedZone CreateAppSyncPrivateHostedZone(Vpc vpc,
        NetworkLoadBalancer nlb, string id)
    {
        var hostedZone = new PrivateHostedZone(this, $"{id}-PrivateHostedZone", new PrivateHostedZoneProps
        {
            Vpc = vpc,
            ZoneName = "appsync-api.us-east-1.amazonaws.com"
        });

        _ = new ARecord(this, $"{id}-PrivateARecord", new ARecordProps
        {
            Zone = hostedZone,
            Target = RecordTarget.FromAlias(new LoadBalancerTarget(nlb))
        });

        return hostedZone;
    }

    private RestApi CreateRestApiWithAppSyncOrigin(string appsyncDomain,
        string path,
        NetworkLoadBalancer nlb, string id)
    {
        var vpcLink = new VpcLink(this, $"{id}-VpcLink", new VpcLinkProps
        {
            Targets = [nlb],
            VpcLinkName = $"{id}-AppSyncApiGatewayPrivate"
        });

        var api = new RestApi(this, $"{id}-AppSyncPrivateApiTest");

        var appsyncResource = api.Root.AddResource(path);
        appsyncResource.AddMethod("ANY", new Integration(
            new IntegrationProps
            {
                Uri = appsyncDomain,
                IntegrationHttpMethod = "POST",
                Type = IntegrationType.HTTP_PROXY,
                Options = new IntegrationOptions
                {
                    ConnectionType = ConnectionType.VPC_LINK,
                    VpcLink = vpcLink
                }
            }
        ));

        return api;
    }

    private string[] GetIpAddressesForVpcEndpoint(InterfaceVpcEndpoint vpcEndpoint,
        int noOfAZs, string id)
    {
        return GetIpsWithAwsCustomResource(
            vpcEndpoint.Node.Id,
            new Dictionary<string, object> { { "NetworkInterfaceIds", vpcEndpoint.VpcEndpointNetworkInterfaceIds } },
            noOfAZs,
            id
        );
    }

    private string[] GetIpsWithAwsCustomResource(string resourceName,
        Dictionary<string, object> parameters,
        int length, string id)
    {
        var name = $"GetIps-{resourceName}";
        var outputPaths = Enumerable.Range(0, length)
            .Select(index => $"NetworkInterfaces.{index}.PrivateIpAddress");
        var getIp = new AwsCustomResource(this, name, new AwsCustomResourceProps
        {
            OnUpdate = new AwsSdkCall
            {
                Service = "EC2",
                Action = "describeNetworkInterfaces",
                OutputPaths = outputPaths.ToArray(),
                Parameters = parameters,
                PhysicalResourceId = PhysicalResourceId.Of(name),
            },
            Policy = AwsCustomResourcePolicy.FromSdkCalls(new SdkCallsPolicyOptions
            {
                Resources = AwsCustomResourcePolicy.ANY_RESOURCE
            }),
            FunctionName = $"{id}-AppSync-GS-Router-GetIpsFromNetworkInterfaces"
        });
        return outputPaths.Select(path => Token.AsString(getIp.GetResponseField(path))).ToArray();
    }
}