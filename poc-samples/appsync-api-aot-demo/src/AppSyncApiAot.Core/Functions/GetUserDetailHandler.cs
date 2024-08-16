using System.ComponentModel.DataAnnotations;
using Amazon.Lambda.Core;
using AppSyncApiAot.Core.Handlers;
using AppSyncApiAot.Core.Models;
using AppSyncApiAot.Infrastructure;
using AppSyncApiAot.Repositories;
using AppSyncApiAot.Repositories.Models;
using Microsoft.Extensions.DependencyInjection;

namespace AppSyncApiAot.Core.Functions;

public class GetUserDetailHandler : AppSyncEventHandler<UserDetail, UserDetail>
{
    private readonly IDynamoDbRepository<UserDetailDto> _userDetailRepository;

    public GetUserDetailHandler()
    {
        _userDetailRepository = ServiceProvider.GetRequiredService<IDynamoDbRepository<UserDetailDto>>();
    }

    protected override string ParentType => "Query";
    protected override string[] FieldNames => ["getUserDetail", "getUserPipeline"];

    protected override Task<bool> Validate(UserDetail request)
    {
        if (string.IsNullOrWhiteSpace(request.UserId))
            throw new ValidationException($"'{nameof(request.UserId)}' cannot be null or empty");

        return Task.FromResult(true);
    }

    protected override async Task<UserDetail> Process(UserDetail request,
        ILambdaContext lambdaContext)
    {
        using var cts = lambdaContext.GetCancellationTokenSource();

        var result = await _userDetailRepository.QueryAsync(request.AsDto(), cts.Token);

        var userDetail = result.Select(dto => new UserDetail
        {
            UserId = dto.UserId,
            FirstName = dto.FirstName,
            LastName = dto.LastName,
        }).First();

        return userDetail;
    }
}