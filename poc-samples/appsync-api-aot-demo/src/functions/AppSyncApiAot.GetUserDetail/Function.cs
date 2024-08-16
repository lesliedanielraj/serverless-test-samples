using System.Text.Json;
using System.Text.Json.Serialization;
using System.Text.Json.Serialization.Metadata;
using Amazon.Lambda.Core;
using Amazon.Lambda.RuntimeSupport;
using Amazon.Lambda.Serialization.SystemTextJson;
using Amazon.Util.Internal;
using AppSyncApiAot.Core.Functions;
using AppSyncApiAot.Core.Models;
using AWS.Lambda.Powertools.Logging;

namespace AppSyncApiAot.GetUserDetail;

public class Function
{
    /// <summary>
    /// The main entry point for the Lambda function. The main function is called once during the Lambda init phase. It
    /// initializes the .NET Lambda runtime client passing in the function handler to invoke for each Lambda event and
    /// the JSON serializer to use for converting Lambda JSON format to the .NET types. 
    /// </summary>
    private static async Task Main()
    {
        var handler = FunctionHandler;
        await LambdaBootstrapBuilder.Create(handler,
                new SourceGeneratorLambdaJsonSerializer<CustomJsonSerializerContext>())
            .Build()
            .RunAsync();
    }

    /// <summary>
    /// A simple function that takes a string and does a ToUpper.
    ///
    /// To use this handler to respond to an AWS event, reference the appropriate package from 
    /// https://github.com/aws/aws-lambda-dotnet#events
    /// and change the string input parameter to the desired event type. When the event type
    /// is changed, the handler type registered in the main method needs to be updated and the CustomJsonSerializerContext 
    /// defined below will need the JsonSerializable updated. If the return type and event type are different than the 
    /// CustomJsonSerializerContext must have two JsonSerializable attributes, one for each type.
    ///
    /// When using Native AOT extra testing with the deployed Lambda functions is required to ensure
    /// the libraries used in the Lambda function work correctly with Native AOT. If a runtime 
    /// error occurs about missing types or methods the most likely solution will be to remove references to trim-unsafe 
    /// code or configure trimming options. This sample defaults to partial TrimMode because currently the AWS 
    /// SDK for .NET does not support trimming. This will result in a larger executable size, and still does not 
    /// guarantee runtime trimming errors won't be hit. 
    /// </summary>
    /// <param name="input">The event for the Lambda function handler to process.</param>
    /// <param name="context">The ILambdaContext that provides methods for logging and describing the Lambda environment.</param>
    /// <returns></returns>
    private static UserDetail FunctionHandler(AppSyncProxyRequest<UserDetail> input, ILambdaContext context)
    {
        Logger.LogInformation(input);
        var fn = new GetUserDetailHandler();
        return new UserDetail();
        // return fn.Handler(input, context).Result;
    }
}

/// <summary>
/// This class is used to register the input event and return type for the FunctionHandler method with the System.Text.Json source generator.
/// There must be a JsonSerializable attribute for each type used as the input and return type or a runtime error will occur 
/// from the JSON serializer unable to find the serialization information for unknown types.
/// </summary>
// [JsonSourceGenerationOptions(
//     GenerationMode = JsonSourceGenerationMode.Metadata,
//     PropertyNameCaseInsensitive = true,
//     PropertyNamingPolicy = JsonKnownNamingPolicy.CamelCase,
//     DictionaryKeyPolicy = JsonKnownNamingPolicy.CamelCase,
//     IncludeFields = true,
//     DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull,
//     UseStringEnumConverter = true)]
// [JsonSourceGenerationOptions(
//     GenerationMode = JsonSourceGenerationMode.Default)]
[JsonSerializable(typeof(AppSyncProxyRequest<UserDetail>))]
[JsonSerializable(typeof(string))]
[JsonSerializable(typeof(object))]
[JsonSerializable(typeof(UserDetail))]
[JsonSerializable(typeof(AppSyncProxyRequest<>.StashContext))]
[JsonSerializable(typeof(AppSyncProxyRequest<>.InfoContext))]
[JsonSerializable(typeof(AppSyncProxyRequest<>.RequestContext))]
[JsonSerializable(typeof(Dictionary<string, string>))]
public partial class CustomJsonSerializerContext : JsonSerializerContext
{
    // By using this partial class derived from JsonSerializerContext, we can generate reflection free JSON Serializer code at compile time
    // which can deserialize our class and properties. However, we must attribute this class to tell it what types to generate serialization code for.
    // See https://docs.microsoft.com/en-us/dotnet/standard/serialization/system-text-json-source-generation
}

// public class CustomLambdaSerializer : DefaultLambdaJsonSerializer
// {
//     public CustomLambdaSerializer() : base(CreateCustomizer())
//     {
//     }
//
//     private static Action<JsonSerializerOptions> CreateCustomizer()
//     {
//         return (JsonSerializerOptions options) =>
//         {
//             options.PropertyNameCaseInsensitive = true;
//             options.DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingDefault;
//             options.DictionaryKeyPolicy = JsonNamingPolicy.CamelCase;
//             // options.TypeInfoResolver = new CustomJsonSerializerContext();
//             options.PropertyNamingPolicy = JsonNamingPolicy.CamelCase;
//             options.ReferenceHandler = ReferenceHandler.Preserve;
//             options.NumberHandling = JsonNumberHandling.Strict;
//             options.TypeInfoResolverChain.Add(new CustomJsonSerializerContext());
//             options.TypeInfoResolverChain.Add(new DefaultJsonTypeInfoResolver());
//             options.TypeInfoResolverChain.Add(new DictionaryStringStringJsonSerializerContexts());
//             options.TypeInfoResolverChain.Add(new DictionaryStringDictionaryStringJsonSerializerContexts());
//             // options.MaxDepth = 3;
//             // options.TypeInfoResolver = new DictionaryStringDictionaryStringJsonSerializerContexts();
//         };
//     }
// }