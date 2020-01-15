local amqp = require("amqp")
local json = require("json")
local base64 = require("base64")

-- Server identifier to tag messages with
local server_id = "testing-area"

local ctx = amqp:new({
    role = 'producer',
    exchange = 'cs2d',
    routing_key = 'chat',
    ssl = false,
})
ctx:connect("rabbitmq", 5672)
ctx:setup()

addhook("say", "__amqp_publish_chat")
function __amqp_publish_chat(id, msg)
    ctx:publish(json.encode({
        serverId = server_id,
        name = player(id, "name"),
        message = msg,
        -- For e.g. web interfaces that want to use this info
        usgn = player(id, "usgn"),
        steamId = player(id, "steamid"),
    }))
end

xch.on("amqp", function(ser)
    local pkt = json.decode(ser)
    if (pkt.routing_key == "chat") then
        local data = json.decode(base64.from(pkt.body))
        -- Don't echo the message to the same server it came from
        if (data.serverId == server_id) then return end
        msg("\169000255000" .. data.name .. " \169175175175(@" .. data.serverId .. ")\169000255000: \169255200000" .. data.message)
    end
end)

addhook("shutdown", "__amqp_cleanup")
function __amqp_cleanup()
    ctx:teardown()
    ctx:close()
end
