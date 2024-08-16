using Amazon.DynamoDBv2;
using Amazon.DynamoDBv2.Model;
using AppSyncApiDemo.Repositories.Helpers;
using AppSyncApiDemo.Repositories.Mappers;
using AppSyncApiDemo.Repositories.Models;
using Microsoft.Extensions.Options;

namespace AppSyncApiDemo.Repositories;

public class UserPreferenceRepository(IAmazonDynamoDB dynamoDbClient, IOptions<ApplicationConfigurationOptions> options)
    : IDynamoDbRepository<UserPreferenceDto>
{
    public async Task<UserPreferenceDto> GetItemAsync(IDictionary<string, string> input,
        CancellationToken cancellationToken)
    {
        var response = await dynamoDbClient.GetItemAsync(
            await SecretsManagerHelper.GetSecretValue(options.Value.PreferenceTableName),
            new Dictionary<string, AttributeValue>(capacity: 1)
            {
                [UserPreferenceMapper.UserId] = new(input["userId"]),
                [UserPreferenceMapper.ApplicationKey] = new(input["applicationKey"]),
            },
            cancellationToken);

        return response.IsItemSet
            ? UserPreferenceMapper.ObjectFromDynamoDb(response.Item)
            : throw new KeyNotFoundException(
                $"User Preference for {input["userId"]}, {input["applicationId"]} & {input["preferenceType"]} not found.");
    }

    public Task<IEnumerable<UserPreferenceDto>> GetItemsAsync(IDictionary<string, string> input,
        CancellationToken cancellationToken)
    {
        throw new NotImplementedException();
    }

    public async Task<UpsertResult> PutItemAsync(UserPreferenceDto dto, CancellationToken cancellationToken)
    {
        var request = new PutItemRequest()
        {
            TableName = await SecretsManagerHelper.GetSecretValue(options.Value.PreferenceTableName),
            Item = UserPreferenceMapper.ObjectToDynamoDb(dto),
            ReturnValues = ReturnValue.ALL_OLD,
        };
        var response = await dynamoDbClient.PutItemAsync(request, cancellationToken);
        var hadOldValues = response.Attributes is not null && response.Attributes.Count > 0;

        return hadOldValues ? UpsertResult.Updated : UpsertResult.Inserted;
    }

    public async Task<bool> DeleteItemAsync(UserPreferenceDto dto, CancellationToken cancellationToken)
    {
        var response = await dynamoDbClient.DeleteItemAsync(
            await SecretsManagerHelper.GetSecretValue(options.Value.PreferenceTableName),
            new Dictionary<string, AttributeValue>(capacity: 1)
            {
                [UserPreferenceMapper.UserId] = new(dto.UserId),
                [UserPreferenceMapper.ApplicationKey] = new(dto.SortKey),
            },
            cancellationToken);

        return response.HttpStatusCode == System.Net.HttpStatusCode.OK;
    }

    public async Task<IEnumerable<UserPreferenceDto>> QueryAsync(UserPreferenceDto dto,
        CancellationToken cancellationToken)
    {
        // Define marker variable
        // Dictionary<string, AttributeValue> startKey = null;
        var result = await dynamoDbClient.QueryAsync(new QueryRequest
        {
            TableName = await SecretsManagerHelper.GetSecretValue(options.Value.PreferenceTableName),
            // ExclusiveStartKey = startKey,
            KeyConditions = new Dictionary<string, Condition>
            {
                // Hash key condition. ComparisonOperator must be "EQ".
                {
                    UserPreferenceMapper.UserId,
                    new Condition
                    {
                        ComparisonOperator = "EQ",
                        AttributeValueList = [new AttributeValue(s: dto.UserId)]
                    }
                },
                // Range key condition
                {
                    UserPreferenceMapper.ApplicationKey,
                    new Condition
                    {
                        ComparisonOperator = "EQ",
                        AttributeValueList = [new AttributeValue(s: dto.SortKey)]
                    }
                }
            }
        }, cancellationToken);

        return result.Items
            .Select(UserPreferenceMapper.ObjectFromDynamoDb);
    }
}