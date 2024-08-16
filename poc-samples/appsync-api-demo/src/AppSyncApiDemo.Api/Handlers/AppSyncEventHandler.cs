using Amazon.Lambda.Core;
using AppSyncApiDemo.Api.Models;
using AWS.Lambda.Powertools.Logging;
using AppSyncApiDemo.Infrastructure;

namespace AppSyncApiDemo.Api.Handlers;

/// <summary>
/// This class abstracts the AWS interaction between AWS AppSync & AWS Lambda Function.
/// </summary>
/// <typeparam name="TRequest">A generic request model</typeparam>
/// <typeparam name="TResponse">A generic output model</typeparam>
public abstract class AppSyncEventHandler<TRequest, TResponse>
{
    protected abstract string ParentType { get; }
    protected abstract string[] FieldNames { get; }
    protected readonly IServiceProvider ServiceProvider;

    protected AppSyncEventHandler() : this(Startup.ServiceProvider)
    {
    }

    private AppSyncEventHandler(IServiceProvider serviceProvider)
    {
        ServiceProvider = serviceProvider;
    }

    /// <summary>
    /// This method is used to perform any validation on the incoming request.
    /// </summary>
    /// <param name="request"></param>
    /// <returns></returns>
    protected abstract Task<bool> Validate(TRequest request);

    /// <summary>
    /// This method is completely abstracted from AWS Infrastructure and is called for every request.
    /// </summary>
    /// <param name="request">Request Object</param>
    /// <param name="lambdaContext">Lambda Context</param>
    /// <returns>TOutput</returns>
    protected abstract Task<TResponse> Process(TRequest request, ILambdaContext lambdaContext);


    /// <summary>
    /// This method is called for every Lambda invocation. This method takes in an AWS AppSync request event object and creates
    /// an event adapter for processing the request.
    /// </summary>
    /// <param name="request">Request Event received by the function handler</param>
    /// <param name="lambdaContext">Lambda Context</param>
    /// <returns></returns>
    [Logging(LogEvent = true, ClearState = true)]
    // [Metrics(Namespace = "AppSyncEventHandler", CaptureColdStart = true)]
    // [Tracing(Namespace = "AppSyncEventHandler", SegmentName = "AppSyncEventHandler",
    //     CaptureMode = TracingCaptureMode.Error)]
    public async Task<TResponse> Handler(
        AppSyncProxyRequest<TRequest> request,
        ILambdaContext lambdaContext)
    {
        try
        {
            // if (request.Info.ParentTypeName != ParentType || request.Stash.Info.ParentTypeName != ParentType)
            //     throw new NotSupportedException(
            //         $"Type {request.Info.ParentTypeName} not allowed! Only {ParentType} allowed for this function");
            //
            // if (!FieldNames.Contains(request.Info.FieldName) || !FieldNames.Contains(request.Stash.Info.FieldName))
            //     throw new NotSupportedException(
            //         $"Type {request.Info.FieldName} not allowed! Only {string.Join(",", FieldNames)} allowed for this function");

            // These abstract methods is implemented by the concrete classes
            await Validate(request.Arguments);
            var response = await Process(request.Arguments, lambdaContext);

            Logger.LogInformation(response);
            return response;
        }
        catch (Exception ex)
        {
            Logger.LogError(ex);
            throw;
        }
    }
}