using System.Collections.Generic;
using System.IO;
using Amazon.CDK;
using Amazon.CDK.AWS.AppSync;
using Amazon.CDK.AWS.DynamoDB;
using Amazon.CDK.AWS.Lambda;
using Amazon.CDK.AWS.Lambda.DotNet;
using Amazon.CDK.AWS.Logs;
using Amazon.CDK.AWS.SecretsManager;
using AppSyncApiAot.Infrastructure.Models;
using Constructs;
using BundlingOptions = Amazon.CDK.AWS.Lambda.DotNet.BundlingOptions;

namespace AppSyncApiAot.Infrastructure.Stacks;

public sealed class AppSyncAotStack : Stack
{
    public string AppSyncDomain { get; set; }

    internal AppSyncAotStack(Construct scope, string id, MultiStackProps props = null) : base(scope, id, props)
    {
        var ddbPreferenceTable = new TableV2(this, $"{id}-user-preference-table", new TablePropsV2
        {
            RemovalPolicy = RemovalPolicy.DESTROY,
            Encryption = TableEncryptionV2.AwsManagedKey(),
            PartitionKey = new Attribute
            {
                Name = "user_id",
                Type = AttributeType.STRING,
            },
            SortKey = new Attribute
            {
                Name = "application_key",
                Type = AttributeType.STRING,
            },
            // LocalSecondaryIndexes =
            // [
            //     new LocalSecondaryIndexProps
            //     {
            //         IndexName = "gsi1",
            //         SortKey = new Attribute
            //         {
            //             Name = "application_id",
            //             Type = AttributeType.STRING
            //         },
            //         ProjectionType = ProjectionType.ALL
            //     },
            //     new LocalSecondaryIndexProps
            //     {
            //         IndexName = "gsi2",
            //         SortKey = new Attribute
            //         {
            //             Name = "preference_type",
            //             Type = AttributeType.STRING
            //         },
            //         ProjectionType = ProjectionType.ALL
            //     },
            // ],
            Billing = Billing.OnDemand(),
            TableName = $"{id}-user-preference-table",
        });

        const string userPreferenceTableName = "user-preference-table-name";
        var secretUserPreferenceTableName = new Secret(this, $"{id}-{userPreferenceTableName}", new SecretProps
        {
            SecretName = $"{id}-{userPreferenceTableName}",
            SecretStringValue = new SecretValue(ddbPreferenceTable.TableName),
            Description = "user preference table name"
        });

        var ddbUserDetailTable = new TableV2(this, $"{id}-user-detail-table", new TablePropsV2
        {
            RemovalPolicy = RemovalPolicy.DESTROY,
            Encryption = TableEncryptionV2.AwsManagedKey(),
            PartitionKey = new Attribute
            {
                Name = "user_id",
                Type = AttributeType.STRING,
            },
            Billing = Billing.OnDemand(),
            TableName = $"{id}-user-detail-table",
        });

        const string userDetailTableName = "user-detail-table-name";
        var secretUserDetailTableName = new Secret(this, $"{id}-{userDetailTableName}", new SecretProps
        {
            SecretName = $"{id}-{userDetailTableName}",
            SecretStringValue = new SecretValue(ddbUserDetailTable.TableName),
            Description = "user detail table name"
        });

        var gqlApi = new GraphqlApi(this, $"{id}-user-preference-api", new GraphqlApiProps
        {
            Name = $"{id}-user-preference-api",
            Visibility = Visibility.PRIVATE,
            XrayEnabled = true,
            LogConfig = new LogConfig
            {
                ExcludeVerboseContent = false,
                FieldLogLevel = FieldLogLevel.ALL,
                Retention = RetentionDays.ONE_WEEK
            },
            Definition = Definition.FromFile(Path.Combine(Directory.GetCurrentDirectory(),
                "src/AppSyncApiAot.Infrastructure/Misc/schema.graphql"))
        });
        AppSyncDomain = gqlApi.GraphqlUrl.Replace("/graphql", "");

        //Lambda Functions

        // var buildOption = new BundlingOptions()
        // {
        //     DockerImage = Runtime.DOTNET_8.BundlingImage,
        //     MsbuildParameters = ["/p:PublishAot=true"],
        // };

        //User Details
        var getUserDetailFunctionName = $"{id}-get-user-detail-function";
        var getUserDetailFunction = new DotNetFunction(this, getUserDetailFunctionName,
            new DotNetFunctionProps()
            {
                FunctionName = getUserDetailFunctionName,
                MemorySize = 1024,
                Timeout = Duration.Seconds(30),
                Runtime = Runtime.DOTNET_8,
                Handler = "AppSyncApiAot.GetUserDetail",
                LogRetention = RetentionDays.ONE_WEEK,
                ProjectDir = "./src/functions/AppSyncApiAot.GetUserDetail/",
                Architecture = Architecture.ARM_64,
                Tracing = Tracing.ACTIVE,
                Environment = new Dictionary<string, string>
                {
                    { "USER_DETAIL_TABLE_NAME", $"{id}-{userDetailTableName}" },
                },
                Bundling = new BundlingOptions
                {
                    DockerImage = Runtime.DOTNET_8.BundlingImage,
                    MsbuildParameters = ["/p:PublishAot=true"],
                }
            });
        var upsertUserDetailFunctionName = $"{id}-save-user-detail-function";
        var upsertUserDetailFunction = new DotNetFunction(this, upsertUserDetailFunctionName,
            new DotNetFunctionProps()
            {
                FunctionName = upsertUserDetailFunctionName,
                MemorySize = 1024,
                Timeout = Duration.Seconds(30),
                Runtime = Runtime.DOTNET_8,
                Handler = "AppSyncApiAot.Core::AppSyncApiAot.Core.Functions.UpsertUserDetailHandler::Handler",
                LogRetention = RetentionDays.ONE_WEEK,
                ProjectDir = "./src/AppSyncApiAot.Core/",
                Architecture = Architecture.X86_64,
                Tracing = Tracing.ACTIVE,
                Environment = new Dictionary<string, string>
                {
                    { "USER_DETAIL_TABLE_NAME", $"{id}-{userDetailTableName}" },
                }
            });

        var getUserDetailFunctionDataSource =
            gqlApi.AddLambdaDataSource($"{id}-get-user-detail-lambda", getUserDetailFunction);
        getUserDetailFunctionDataSource.CreateResolver($"{id}-get-user-detail-resolver", new ResolverProps
        {
            Api = gqlApi,
            TypeName = "Query",
            FieldName = "getUserDetail",
            RequestMappingTemplate = MappingTemplate.LambdaRequest(),
            ResponseMappingTemplate = MappingTemplate.LambdaResult(),
        });
        var upsertUserDetailFunctionDataSource =
            gqlApi.AddLambdaDataSource($"{id}-upsert-user-detail-lambda", upsertUserDetailFunction);
        upsertUserDetailFunctionDataSource.CreateResolver($"{id}-upsert-user-detail-resolver", new ResolverProps
        {
            Api = gqlApi,
            TypeName = "Mutation",
            FieldName = "upsertUserDetail",
            RequestMappingTemplate = MappingTemplate.LambdaRequest(),
            ResponseMappingTemplate = MappingTemplate.LambdaResult(),
        });

        //User Preference
        var getUserPreferenceFunctionName = $"{id}-get-user-preference-function";
        var getUserPreferenceFunction = new DotNetFunction(this, getUserPreferenceFunctionName,
            new DotNetFunctionProps()
            {
                FunctionName = getUserPreferenceFunctionName,
                MemorySize = 1024,
                Timeout = Duration.Seconds(30),
                Runtime = Runtime.DOTNET_8,
                Handler = "AppSyncApiAot.Core::AppSyncApiAot.Core.Functions.GetUserPreferenceFunction::Handler",
                LogRetention = RetentionDays.ONE_WEEK,
                ProjectDir = "./src/AppSyncApiAot.Core/",
                Architecture = Architecture.X86_64,
                Tracing = Tracing.ACTIVE,
                Environment = new Dictionary<string, string>
                {
                    { "PREFERENCE_TABLE_NAME", $"{id}-{userPreferenceTableName}" },
                }
            });
        var upsertUserPreferenceFunctionName = $"{id}-save-user-preference-function";
        var upsertUserPreferenceFunction = new DotNetFunction(this, upsertUserPreferenceFunctionName,
            new DotNetFunctionProps()
            {
                FunctionName = upsertUserPreferenceFunctionName,
                MemorySize = 1024,
                Timeout = Duration.Seconds(30),
                Runtime = Runtime.DOTNET_8,
                Handler = "AppSyncApiAot.Core::AppSyncApiAot.Core.Functions.UpsertUserPreferenceFunction::Handler",
                LogRetention = RetentionDays.ONE_WEEK,
                ProjectDir = "./src/AppSyncApiAot.Core/",
                Architecture = Architecture.X86_64,
                Tracing = Tracing.ACTIVE,
                Environment = new Dictionary<string, string>
                {
                    { "PREFERENCE_TABLE_NAME", $"{id}-{userPreferenceTableName}" },
                }
            });
        var deleteUserPreferenceFunctionName = $"{id}-delete-user-preference-function";
        var deleteUserPreferenceFunction = new DotNetFunction(this, deleteUserPreferenceFunctionName,
            new DotNetFunctionProps()
            {
                FunctionName = deleteUserPreferenceFunctionName,
                MemorySize = 1024,
                Timeout = Duration.Seconds(30),
                Runtime = Runtime.DOTNET_8,
                Handler = "AppSyncApiAot.Core::AppSyncApiAot.Core.Functions.DeleteUserPreferenceFunction::Handler",
                LogRetention = RetentionDays.ONE_WEEK,
                ProjectDir = "./src/AppSyncApiAot.Core/",
                Architecture = Architecture.X86_64,
                Tracing = Tracing.ACTIVE,
                Environment = new Dictionary<string, string>
                {
                    { "PREFERENCE_TABLE_NAME", $"{id}-{userPreferenceTableName}" },
                }
            });

        var getUserPreferenceFunctionDataSource =
            gqlApi.AddLambdaDataSource($"{id}-get-user-preference-lambda", getUserPreferenceFunction);
        getUserPreferenceFunctionDataSource.CreateResolver($"{id}-get-user-preference-resolver", new ResolverProps
        {
            Api = gqlApi,
            TypeName = "Query",
            FieldName = "getUserPreference",
            RequestMappingTemplate = MappingTemplate.LambdaRequest(),
            ResponseMappingTemplate = MappingTemplate.LambdaResult(),
        });
        var upsertUserPreferenceFunctionDataSource =
            gqlApi.AddLambdaDataSource($"{id}-upsert-user-preference-lambda", upsertUserPreferenceFunction);
        upsertUserPreferenceFunctionDataSource.CreateResolver($"{id}-upsert-user-preference-resolver", new ResolverProps
        {
            Api = gqlApi,
            TypeName = "Mutation",
            FieldName = "upsertUserPreference",
            RequestMappingTemplate = MappingTemplate.LambdaRequest(),
            ResponseMappingTemplate = MappingTemplate.LambdaResult(),
        });
        var deleteUserPreferenceFunctionDataSource =
            gqlApi.AddLambdaDataSource($"{id}-delete-user-preference-lambda", deleteUserPreferenceFunction);
        deleteUserPreferenceFunctionDataSource.CreateResolver($"{id}-delete-user-preference-resolver", new ResolverProps
        {
            Api = gqlApi,
            TypeName = "Mutation",
            FieldName = "deleteUserPreference",
            RequestMappingTemplate = MappingTemplate.LambdaRequest(),
            ResponseMappingTemplate = MappingTemplate.LambdaResult(),
        });

        //Pipeline
        var fn1 = new AppsyncFunction(this, $"{id}-get-user-detail-appsync-function", new AppsyncFunctionProps
        {
            Api = gqlApi,
            Name = "getUserDetailAppSyncFunction",
            DataSource = getUserDetailFunctionDataSource,
            RequestMappingTemplate = MappingTemplate.LambdaRequest(),
            // ResponseMappingTemplate = MappingTemplate.LambdaResult()
            // RequestMappingTemplate = MappingTemplate.FromFile(Path.Combine(Directory.GetCurrentDirectory(),
                // "src/AppSyncApiAot.Infrastructure/Vtl/Query.GetUserDetail.Request.vtl")),
            ResponseMappingTemplate = MappingTemplate.FromFile(Path.Combine(Directory.GetCurrentDirectory(),
                "src/AppSyncApiAot.Infrastructure/Vtl/Query.GetUserDetail.Response.vtl")),
        });
        var fn2 = new AppsyncFunction(this, $"{id}-get-user-preference-appsync-function", new AppsyncFunctionProps
        {
            Api = gqlApi,
            Name = "getUserPreferenceAppSyncFunction",
            DataSource = getUserPreferenceFunctionDataSource,
            // RequestMappingTemplate = MappingTemplate.LambdaRequest(),
            // ResponseMappingTemplate = MappingTemplate.LambdaResult(),
            RequestMappingTemplate = MappingTemplate.FromFile(Path.Combine(Directory.GetCurrentDirectory(),
                "src/AppSyncApiAot.Infrastructure/Vtl/Query.GetUserPreference.Request.vtl")),
            ResponseMappingTemplate = MappingTemplate.FromFile(Path.Combine(Directory.GetCurrentDirectory(),
                "src/AppSyncApiAot.Infrastructure/Vtl/Query.GetUserPreference.Response.vtl")),
        });

        // var noneDataSource = gqlApi.AddNoneDataSource($"{id}-none-data-source", new DataSourceOptions
        // {
        //     Name = "noneDataSource",
        //     Description = "Used for pipeline resolver"
        // });
        gqlApi.CreateResolver($"{id}-get-user-pipeline-resolver", new ResolverProps
        {
            Api = gqlApi,
            TypeName = "Query",
            FieldName = "getUserPipeline",
            PipelineConfig = [fn1, fn2],
            // RequestMappingTemplate = MappingTemplate.LambdaRequest(),
            // ResponseMappingTemplate = MappingTemplate.LambdaResult(),
            RequestMappingTemplate = MappingTemplate.FromFile(Path.Combine(Directory.GetCurrentDirectory(),
                "src/AppSyncApiAot.Infrastructure/Vtl/Query.GetUserPipeline.Request.vtl")),
            ResponseMappingTemplate = MappingTemplate.FromFile(Path.Combine(Directory.GetCurrentDirectory(),
                "src/AppSyncApiAot.Infrastructure/Vtl/Query.GetUserPipeline.Response.vtl")),
        });

        //Permissions
        ddbPreferenceTable.GrantReadData(getUserPreferenceFunction);
        ddbPreferenceTable.GrantReadWriteData(upsertUserPreferenceFunction);
        ddbPreferenceTable.GrantReadWriteData(deleteUserPreferenceFunction);
        ddbUserDetailTable.GrantReadData(getUserDetailFunction);
        ddbUserDetailTable.GrantReadWriteData(upsertUserDetailFunction);

        secretUserPreferenceTableName.GrantRead(getUserPreferenceFunction);
        secretUserPreferenceTableName.GrantRead(deleteUserPreferenceFunction);
        secretUserPreferenceTableName.GrantRead(upsertUserPreferenceFunction);
        secretUserDetailTableName.GrantRead(getUserDetailFunction);
        secretUserDetailTableName.GrantRead(upsertUserDetailFunction);

        //Outputs
        _ = new CfnOutput(this, "AppSyncApi", new CfnOutputProps
        {
            Value = gqlApi.GraphqlUrl,
            Description = "AppSyncApi GraphqlUrl"
        });

        _ = new CfnOutput(this, "UserDetailTableName", new CfnOutputProps
        {
            Value = ddbUserDetailTable.TableName,
            Description = "User Detail Table Name"
        });

        _ = new CfnOutput(this, "GetUserDetailFunction", new CfnOutputProps
        {
            Value = getUserDetailFunction.FunctionArn,
            Description = "Get User Detail Function ARN"
        });

        _ = new CfnOutput(this, "UpsertUserDetailFunction", new CfnOutputProps
        {
            Value = upsertUserDetailFunction.FunctionArn,
            Description = "Upsert User Detail Function ARN"
        });

        _ = new CfnOutput(this, "PreferenceTableName", new CfnOutputProps
        {
            Value = ddbPreferenceTable.TableName,
            Description = "Preference Table Name"
        });

        _ = new CfnOutput(this, "GetUserPreferenceFunction", new CfnOutputProps
        {
            Value = getUserPreferenceFunction.FunctionArn,
            Description = "Get User Preference Function ARN"
        });

        _ = new CfnOutput(this, "UpsertUserPreferenceFunction", new CfnOutputProps
        {
            Value = upsertUserPreferenceFunction.FunctionArn,
            Description = "Upsert User Preference Function ARN"
        });

        _ = new CfnOutput(this, "DeleteUserPreferenceFunction", new CfnOutputProps
        {
            Value = deleteUserPreferenceFunction.FunctionArn,
            Description = "Delete User Preference Function ARN"
        });
    }
}