# 方法1：直接在命令行测试 Redis 连接
# redis-cli -h 127.0.0.1 -p 6379 -a wzCTMV!IQEllCSr ping

# 方法2：Python 测试连接
import redis

try:
    r = redis.Redis(
        host='127.0.0.1',
        port=6379,
        password='123456',
        db=1,
        decode_responses=True
    )
    response = r.ping()
    print(f"Redis connection successful: {response}")
except Exception as e:
    print(f"Redis connection failed: {e}")
