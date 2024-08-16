using Amazon.DynamoDBv2;
using Amazon.DynamoDBv2.Model;
using AppSyncApiAot.Repositories.Helpers;
using AppSyncApiAot.Repositories.Mappers;
using AppSyncApiAot.Repositories.Models;
using Microsoft.Extensions.Options;

namespace AppSyncApiAot.Repositories;

public class UserDetailRepository(IAmazonDynamoDB dynamoDbClient, IOptions<ApplicationConfigurationOptions> options)
    : IDynamoDbRepository<UserDetailDto>
{
    public async Task<UserDetailDto> GetItemAsync(IDictionary<string, string> input,
        CancellationToken cancellationToken)
    {
        var response = await dynamoDbClient.GetItemAsync(
            await SecretsManagerHelper.GetSecretValue(options.Value.UserDetailTableName),
            new Dictionary<string, AttributeValue>(capacity: 1)
            {
                [UserDetailMapper.UserId] = new(input["userId"]),
                [UserDetailMapper.FirstName] = new(input["firstName"]),
                [UserDetailMapper.LastName] = new(input["lastName"]),
            },
            cancellationToken);

        return response.IsItemSet
            ? UserDetailMapper.ObjectFromDynamoDb(response.Item)
            : throw new KeyNotFoundException(
                $"User Detail for {input["userId"]} not found.");
    }

    public Task<IEnumerable<UserDetailDto>> GetItemsAsync(IDictionary<string, string> input,
        CancellationToken cancellationToken)
    {
        throw new NotImplementedException();
    }

    public async Task<UpsertResult> PutItemAsync(UserDetailDto dto, CancellationToken cancellationToken)
    {
        var request = new PutItemRequest()
        {
            TableName = await SecretsManagerHelper.GetSecretValue(options.Value.UserDetailTableName),
            Item = UserDetailMapper.ObjectToDynamoDb(dto),
            ReturnValues = ReturnValue.ALL_OLD,
        };
        var response = await dynamoDbClient.PutItemAsync(request, cancellationToken);
        var hadOldValues = response.Attributes is not null && response.Attributes.Count > 0;

        return hadOldValues ? UpsertResult.Updated : UpsertResult.Inserted;
    }

    public async Task<bool> DeleteItemAsync(UserDetailDto dto, CancellationToken cancellationToken)
    {
        var response = await dynamoDbClient.DeleteItemAsync(
            await SecretsManagerHelper.GetSecretValue(options.Value.UserDetailTableName),
            new Dictionary<string, AttributeValue>(capacity: 1)
            {
                [UserDetailMapper.UserId] = new(dto.UserId),
            },
            cancellationToken);

        return response.HttpStatusCode == System.Net.HttpStatusCode.OK;
    }

    public async Task<IEnumerable<UserDetailDto>> QueryAsync(UserDetailDto dto,
        CancellationToken cancellationToken)
    {
        // Define marker variable
        // Dictionary<string, AttributeValue> startKey = null;
        var result = await dynamoDbClient.QueryAsync(new QueryRequest
        {
            TableName = await SecretsManagerHelper.GetSecretValue(options.Value.UserDetailTableName),
            // ExclusiveStartKey = startKey,
            KeyConditions = new Dictionary<string, Condition>
            {
                // Hash key condition. ComparisonOperator must be "EQ".
                {
                    UserDetailMapper.UserId,
                    new Condition
                    {
                        ComparisonOperator = "EQ",
                        AttributeValueList = [new AttributeValue(s: dto.UserId)]
                    }
                }
            }
        }, cancellationToken);

        return result.Items
            .Select(UserDetailMapper.ObjectFromDynamoDb);
    }
}