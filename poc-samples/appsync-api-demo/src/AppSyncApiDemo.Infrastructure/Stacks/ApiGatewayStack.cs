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
using AppSyncApiDemo.Infrastructure.Models;
using Constructs;

namespace AppSyncApiDemo.Infrastructure.Stacks;

public sealed class ApiGatewayStack : Stack
{
    internal ApiGatewayStack(Construct scope, string id, MultiStackProps props = null) : base(scope, id, props)
    {
        var vpc = CreateVpc(
            props.VpcCidr,
            props.NumberOfAZs
        );
        var vpcEndpoint = CreateAppSyncVpcEndpoint(vpc);
        var nlb = CreateNetworkLoadBalancerTargetingVpcEndpoint(
            vpc,
            vpcEndpoint,
            props.NumberOfAZs
        );
        var hostedZone = CreateAppSyncPrivateHostedZone(vpc, nlb);
        var restApi = CreateRestApiWithAppSyncOrigin(
            props.AppSyncDomain,
            props.AppSyncGatewayPath,
            nlb
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

    private Vpc CreateVpc(string vpcCidr, int noOfAzs)
    {
        return new Vpc(this, "AppSyncApiGatewayVpc", new VpcProps
        {
            IpAddresses = IpAddresses.Cidr(vpcCidr),
            MaxAzs = noOfAzs,
            VpcName = "AppSyncApiGatewayVpc",
            SubnetConfiguration =
            [
                new SubnetConfiguration
                {
                    Name = "gs-router-isolated",
                    SubnetType = SubnetType.PRIVATE_ISOLATED,
                    CidrMask = 22
                }
            ]
        });
    }

    private static InterfaceVpcEndpoint CreateAppSyncVpcEndpoint(Vpc vpc)
    {
        return vpc.AddInterfaceEndpoint("AppSyncVpcEndpoint", new InterfaceVpcEndpointProps
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
    }

    private NetworkLoadBalancer CreateNetworkLoadBalancerTargetingVpcEndpoint(
        Vpc vpc,
        InterfaceVpcEndpoint vpcEndpoint,
        int noOfAZs)
    {
        var ipAddresses = GetIpAddressesForVpcEndpoint(vpcEndpoint, noOfAZs);

        var nlb = new NetworkLoadBalancer(this, "AppSyncApiGatewayNLB", new NetworkLoadBalancerProps
        {
            Vpc = vpc,
            InternetFacing = false,
            LoadBalancerName = "AppSyncApiGatewayNlb",
            VpcSubnets = new SubnetSelection
            {
                SubnetType = SubnetType.PRIVATE_ISOLATED
            }
        });

        var nlbListener = nlb.AddListener("AppSyncApiGatewayNLBListener", new NetworkListenerProps
        {
            Port = 443
        });

        nlbListener.AddTargets("AppSyncApiGatewayNLBTargetGroup", new AddNetworkTargetsProps
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

    private PrivateHostedZone CreateAppSyncPrivateHostedZone(
        Vpc vpc,
        NetworkLoadBalancer nlb)
    {
        var hostedZone = new PrivateHostedZone(this, "AppSyncApiGatewayPrivateHostedZone", new PrivateHostedZoneProps
        {
            Vpc = vpc,
            ZoneName = "appsync-api.us-east-1.amazonaws.com"
        });

        _ = new ARecord(this, "AppSyncApiGatewayPrivateARecord", new ARecordProps
        {
            Zone = hostedZone,
            Target = RecordTarget.FromAlias(new LoadBalancerTarget(nlb))
        });

        return hostedZone;
    }

    private RestApi CreateRestApiWithAppSyncOrigin(
        string appsyncDomain,
        string path,
        NetworkLoadBalancer nlb)
    {
        var vpcLink = new VpcLink(this, "VpcLink", new VpcLinkProps
        {
            Targets = [nlb],
            VpcLinkName = "AppSyncApiGatewayPrivate"
        });

        var api = new RestApi(this, "AppSyncPrivateApiTest");

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

    private string[] GetIpAddressesForVpcEndpoint(
        InterfaceVpcEndpoint vpcEndpoint,
        int noOfAZs)
    {
        return GetIpsWithAwsCustomResource(
            vpcEndpoint.Node.Id,
            new Dictionary<string, object> { { "NetworkInterfaceIds", vpcEndpoint.VpcEndpointNetworkInterfaceIds } },
            noOfAZs // ToDo: make this dynamic
        );
    }

    private string[] GetIpsWithAwsCustomResource(
        string resourceName,
        Dictionary<string, object> parameters,
        int length)
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
            FunctionName = "AppSync-GS-Router-GetIpsFromNetworkInterfaces"
        });
        return outputPaths.Select(path => Token.AsString(getIp.GetResponseField(path))).ToArray();
    }
}