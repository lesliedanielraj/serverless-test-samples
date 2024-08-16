using Amazon.Lambda.Core;
using Amazon.Lambda.Serialization.SystemTextJson;

// Assembly attribute to enable the Lambda function's JSON request to be converted into a .NET class.
[assembly: LambdaSerializer(typeof(CamelCaseLambdaJsonSerializer))]
