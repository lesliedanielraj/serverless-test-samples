using System.ComponentModel.DataAnnotations;
using Amazon.Lambda.Core;
using AppSyncApiDemo.Api.Handlers;
using AppSyncApiDemo.Api.Models;
using AppSyncApiDemo.Infrastructure;
using AppSyncApiDemo.Repositories;
using AppSyncApiDemo.Repositories.Models;
using Microsoft.Extensions.DependencyInjection;

namespace AppSyncApiDemo.Api.Functions;

public class DeleteUserPreferenceFunction : AppSyncEventHandler<UserPreference, bool>
{
    private readonly IDynamoDbRepository<UserPreferenceDto> _userPreferenceRepository;

    public DeleteUserPreferenceFunction()
    {
        _userPreferenceRepository = ServiceProvider.GetRequiredService<IDynamoDbRepository<UserPreferenceDto>>();
    }

    protected override string ParentType => "Mutation";
    protected override string[] FieldNames => ["deleteUserPreference"];

    protected override Task<bool> Validate(UserPreference request)
    {
        if (string.IsNullOrWhiteSpace(request.UserId))
            throw new ValidationException($"'{nameof(request.UserId)}' cannot be null or empty");
        if (request.ApplicationKey.Count <= 0)
            throw new ValidationException($"'{nameof(request.ApplicationKey)}' cannot be null or empty");

        return Task.FromResult(true);
    }

    protected override async Task<bool> Process(
        UserPreference request,
        ILambdaContext lambdaContext)
    {
        using var cts = lambdaContext.GetCancellationTokenSource();

        return await _userPreferenceRepository.DeleteItemAsync(request.AsDto(), cts.Token);
    }
}