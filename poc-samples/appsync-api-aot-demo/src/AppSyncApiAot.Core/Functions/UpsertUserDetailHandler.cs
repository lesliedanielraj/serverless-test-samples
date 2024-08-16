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

public class UpsertUserDetailHandler : AppSyncEventHandler<UserDetail, UpsertResult>
{
    private readonly IDynamoDbRepository<UserDetailDto> _userDetailRepository;

    public UpsertUserDetailHandler()
    {
        _userDetailRepository = ServiceProvider.GetRequiredService<IDynamoDbRepository<UserDetailDto>>();
    }

    protected override string ParentType => "Mutation";
    protected override string[] FieldNames => ["upsertUserDetail"];


    protected override Task<bool> Validate(UserDetail request)
    {
        if (string.IsNullOrWhiteSpace(request.UserId))
            throw new ValidationException($"'{nameof(request.UserId)}' cannot be null or empty");
        if (string.IsNullOrWhiteSpace(request.FirstName))
            throw new ValidationException($"'{nameof(request.FirstName)}' cannot be null or empty");
        if (string.IsNullOrWhiteSpace(request.LastName))
            throw new ValidationException($"'{nameof(request.LastName)}' cannot be null or empty");

        return Task.FromResult(true);
    }

    protected override async Task<UpsertResult> Process(UserDetail request, ILambdaContext lambdaContext)
    {
        using var cts = lambdaContext.GetCancellationTokenSource();
        return await _userDetailRepository.PutItemAsync(request.AsDto(), cts.Token);
    }
}