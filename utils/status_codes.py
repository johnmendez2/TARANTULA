class StatusCodes:
    # Task stage
    SUCCESS         = "TA_000"
    PENDING         = "TA_001" 
    INPROGRESS      = "TA_002"
    
    # Client
    INVALID_REQUEST                 =  "TA_400" # Empty, null, invalid filed in payload
    EXCEEDING_PERMITTED_RESOURCES   = "TA_401"  # < 300s is permitted
    RESOURCE_DOES_NOT_EXIST         = "TA_402"  # Can not find melody for exmaple
    UNSUPPORTED                     = "TA_403"  # Type of resource: melody must be *mp3

    # Server
    TIMEOUT         = "TA_500" # If a task exceeding timeout => Set status timeout
    ERROR           = "TA_501" # unknown ERROR
    RABBIT_ERROR    = "TA_502" # Service cannot connect to Rabbit
    REDIS_ERROR     = "TA_303" # Service cannot connect to Redis
    S3_ERROR        = "TA_504" # Service cannot connect to S3
    ALREADYEXISTS   = "TA_505"