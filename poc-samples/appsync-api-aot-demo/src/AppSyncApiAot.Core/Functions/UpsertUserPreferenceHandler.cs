using System.ComponentModel.DataAnnotations;
using Amazon.Lambda.Core;
using AppSyncApiAot.Core.Handlers;
using AppSyncApiAot.Core.Models;
using AppSyncApiAot.Infrastructure;
using AppSyncApiAot.Repositories;
using AppSyncApiAot.Repositories.Mappers;
using AppSyncApiAot.Repositories.Models;
using Microsoft.Extensions.DependencyInjection;

namespace AppSyncApiAot.Core.Functions;

public class UpsertUserPreferenceHandler : AppSyncEventHandler<UserPreference, UpsertResult>
{
    private readonly IDynamoDbRepository<UserPreferenceDto> _userPreferenceRepository;

    public UpsertUserPreferenceHandler()
    {
        _userPreferenceRepository = ServiceProvider.GetRequiredService<IDynamoDbRepository<UserPreferenceDto>>();
    }

    protected override string ParentType => "Mutation";
    protected override string[] FieldNames => ["upsertUserPreference"];


    protected override Task<bool> Validate(UserPreference request)
    {
        if (string.IsNullOrWhiteSpace(request.UserId))
            throw new ValidationException($"'{nameof(request.UserId)}' cannot be null or empty");
        if (request.ApplicationKey.Count <= 0)
            throw new ValidationException($"'{nameof(request.ApplicationKey)}' cannot be null or empty");

        if (request.Preference == null)
            throw new ValidationException($"'{nameof(request.Preference)}' cannot be null");

        return Task.FromResult(true);
    }

    protected override async Task<UpsertResult> Process(UserPreference request, ILambdaContext lambdaContext)
    {
        using var cts = lambdaContext.GetCancellationTokenSource();
        return await _userPreferenceRepository.PutItemAsync(request.AsDto(), cts.Token);
    }
}