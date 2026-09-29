local capacity = tonumber(ARGV[1])
local refill_rate = tonumber(ARGV[2])
local ttl = tonumber(ARGV[3])

local current_time = tonumber(redis.call('TIME')[1])

local tokens = redis.call("HGET", KEYS[1], "tokens")

local last_refill = redis.call("HGET", KEYS[1], "last_refill")


if not tokens then 
    tokens = capacity
    last_refill = current_time
else
    tokens = tonumber(tokens)
    last_refill = tonumber(last_refill)
    local elapsed = current_time-last_refill
    local to_add = elapsed*refill_rate
    tokens = math.min(tokens+to_add,capacity)
    last_refill = current_time
end
local allowed = 0
if tokens>=1 then
    tokens=tokens-1
    allowed = 1
end

redis.call("HSET", KEYS[1], "tokens", tokens, "last_refill", last_refill)
    redis.call("EXPIRE", KEYS[1], ttl)

return allowed
