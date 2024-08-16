using System.ComponentModel.DataAnnotations;
using Amazon.Lambda.Core;
using AppSyncApiDemo.Api.Handlers;
using AppSyncApiDemo.Api.Models;
using AppSyncApiDemo.Infrastructure;
using AppSyncApiDemo.Repositories;
using AppSyncApiDemo.Repositories.Models;
using Microsoft.Extensions.DependencyInjection;

namespace AppSyncApiDemo.Api.Functions;

public class GetUserPreferenceFunction : AppSyncEventHandler<UserPreference, IEnumerable<UserPreference>>
{
    private readonly IDynamoDbRepository<UserPreferenceDto> _userPreferenceRepository;

    public GetUserPreferenceFunction()
    {
        _userPreferenceRepository = ServiceProvider.GetRequiredService<IDynamoDbRepository<UserPreferenceDto>>();
    }

    protected override string ParentType => "Query";
    protected override string[] FieldNames => ["getUserPreference", "getUserPipeline"];


    protected override Task<bool> Validate(UserPreference request)
    {
        if (string.IsNullOrWhiteSpace(request.UserId))
            throw new ValidationException($"'{nameof(request.UserId)}' cannot be null or empty");
        if (request.ApplicationKey.Count <= 0)
            throw new ValidationException($"'{nameof(request.ApplicationKey)}' cannot be null or empty");

        return Task.FromResult(true);
    }

    protected override async Task<IEnumerable<UserPreference>> Process(UserPreference request,
        ILambdaContext lambdaContext)
    {
        using var cts = lambdaContext.GetCancellationTokenSource();

        var result = await _userPreferenceRepository.QueryAsync(request.AsDto(), cts.Token);

        var userPreferences = result.Select(dto => new UserPreference
        {
            UserId = dto.UserId,
            ApplicationKey = dto.ApplicationKey,
            Preference = dto.Preference,
        });

        return userPreferences;
    }
}