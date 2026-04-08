"""
修改任务指令：你想在附近1.2公里内找一家银行网点。你打算从这家银行打车去徐州东站赶高铁，所以从银行开车到徐州东站的时间必须不超过20分钟。另外你自己走到银行的时间要在20分钟以内，而且你还希望满足一个时间上的关系：从银行开车去徐州东站所花的时间要比你走到银行的时间更长。你说话简短急促，希望快速完成所有事。
# 注意：首个约束已修正为"你想在附近1.2公里内找一家银行网点"（强调"附近指定距离内"，而非"不超过指定距离"）

根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 调用 maps_around_search(location='117.200842,34.210638', radius='1200', keywords='银行')，验证返回pois中包含 target_poi_id=B020402B75（验证"附近1.2公里内的银行"）  
2) 调用 maps_search_detail(id='B020402B75') 获取目标POI的location='117.194026,34.210794'  
3) 调用 maps_geo(address='徐州东站', city='徐州') 获取徐州东站坐标 destination='117.306044,34.267951'  
4) 调用 maps_driving_by_coordinates(origin='117.194026,34.210794', destination='117.306044,34.267951')，验证 total_duration_seconds <= 1200（验证"到徐州东站驾车≤20分钟"）  
5) 调用 maps_walking_by_coordinates(origin='117.200842,34.210638', destination='117.194026,34.210794')，验证 total_duration_seconds <= 1200（验证"步行到银行≤20分钟"）  
6) 验证时间拓扑关系：步骤4的驾车 total_duration_seconds > 步骤5的步行 total_duration_seconds
"""

import os
import sys

# 将 src 加入 sys.path，以便从 src/tools/amap_tools 导入
_current_file_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_current_file_dir)
_src_dir = os.path.join(_project_root, "src")
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

# 导入高德地图工具函数
from tools.amap_tools import (
    maps_search_detail,
    maps_walking_by_coordinates,
    maps_driving_by_coordinates,
    maps_geo
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str,
    user_location: str = "117.200842,34.210638",
    bank_location: str = None,
    search_radius: int = 1200,
    keywords: str = "银行",
    station_address: str = "徐州东站",
    station_city: str = "徐州",
    station_location: str = None,
    max_driving_duration: int = 1200,  # 20分钟 = 1200秒
    max_walking_duration: int = 1200  # 20分钟 = 1200秒
) -> bool:
    """
    验证POI是否符合要求
    
    验证步骤：
    1) 调用 maps_around_search，验证返回pois中包含目标poi_id（验证"附近1.2公里内的银行"）。
    2) 调用 maps_search_detail 获取目标POI的location。
    3) 调用 maps_geo 获取徐州东站坐标。
    4) 调用 maps_driving_by_coordinates，验证 total_duration_seconds <= 1200（验证"到徐州东站驾车≤20分钟"）。
    5) 调用 maps_walking_by_coordinates，验证 total_duration_seconds <= 1200（验证"步行到银行≤20分钟"）。
    6) 验证时间拓扑关系：步骤4的驾车 total_duration_seconds > 步骤5的步行 total_duration_seconds。
    
    Args:
        poi_id: POI ID，默认"B020402B75"
        user_location: 用户坐标，格式为"经度,纬度"，默认"117.200842,34.210638"
        bank_location: 银行坐标，格式为"经度,纬度"，如果为None则从POI详情中获取
        search_radius: 搜索半径（米），默认1200（1.2公里）
        keywords: 搜索关键词，默认"银行"
        station_address: 火车站地址，默认"徐州东站"
        station_city: 火车站所在城市，默认"徐州"
        station_location: 火车站坐标，格式为"经度,纬度"，如果为None则从maps_geo获取
        max_driving_duration: 最大驾车时长（秒），默认1200（20分钟）
        max_walking_duration: 最大步行时长（秒），默认1200（20分钟）
    
    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 周边约束验证
    print(f"【步骤1】验证周边约束（{search_radius}米范围内，关键词：{keywords}）")
    print("-" * 80)
    around_search_result = maps_around_search(
        location=user_location,
        radius=str(search_radius),
        keywords=keywords
    )
    if around_search_result.error:
        print(f"❌ 搜索周边POI失败: {around_search_result.error}")
        return False
    
    if not around_search_result.pois:
        print(f"❌ 未找到符合条件的POI")
        return False
    
    # 检查返回列表中是否包含目标POI ID
    poi_found = False
    for poi in around_search_result.pois:
        if poi.id == poi_id:
            poi_found = True
            print(f"✅ 在{search_radius}米范围内找到目标POI: {poi.name} (ID: {poi_id})")
            break
    
    if not poi_found:
        print(f"❌ 目标POI {poi_id} 不在{search_radius}米范围内的{keywords}列表中")
        return False
    
    # 步骤2: 获取目标POI的location
    print(f"\n【步骤2】获取目标POI的location")
    print("-" * 80)
    bank_detail = maps_search_detail(id=poi_id)
    if bank_detail.error:
        print(f"❌ 获取银行详情失败: {bank_detail.error}")
        return False
    
    if bank_detail.location:
        bank_location = bank_detail.location
        print(f"✅ 获取银行坐标: {bank_location} ({bank_detail.name})")
    else:
        if bank_location is None:
            print(f"❌ POI没有location信息")
            return False
        print(f"⚠️  银行详情中没有location信息，使用传入的默认坐标: {bank_location}")
    
    # 步骤3: 获取徐州东站坐标
    print(f"\n【步骤3】获取徐州东站坐标")
    print("-" * 80)
    geo_result = maps_geo(address=station_address, city=station_city)
    if geo_result.error:
        print(f"❌ 获取火车站坐标失败: {geo_result.error}")
        return False
    
    if not geo_result.results or len(geo_result.results) == 0:
        print(f"❌ 未找到火车站坐标")
        return False
    
    station_location = geo_result.results[0].location
    print(f"✅ 获取火车站坐标: {station_location} ({station_address})")
    
    # 步骤4: 银行到火车站驾车时间约束
    print(f"\n【步骤4】验证银行到火车站驾车时间约束（<={max_driving_duration}秒，即{max_driving_duration // 60}分钟）")
    print("-" * 80)
    driving_result = maps_driving_by_coordinates(
        origin=bank_location,
        destination=station_location
    )
    if driving_result.error:
        print(f"❌ 计算驾车路线失败: {driving_result.error}")
        return False
    
    if driving_result.total_duration_seconds is None:
        print(f"❌ 无法获取驾车时长")
        return False
    
    driving_duration = driving_result.total_duration_seconds
    if driving_duration > max_driving_duration:
        print(f"❌ 驾车时长{driving_duration}秒，超过{max_driving_duration}秒（{max_driving_duration // 60}分钟）")
        return False
    print(f"✅ 驾车时长{driving_duration}秒，符合要求（<= {max_driving_duration}秒，即{max_driving_duration // 60}分钟）")
    
    # 步骤5: 用户到银行步行时间约束
    print(f"\n【步骤5】验证用户到银行步行时间约束（<={max_walking_duration}秒，即{max_walking_duration // 60}分钟）")
    print("-" * 80)
    walking_result = maps_walking_by_coordinates(
        origin=user_location,
        destination=bank_location
    )
    if walking_result.error:
        print(f"❌ 计算步行路线失败: {walking_result.error}")
        return False
    
    if walking_result.total_duration_seconds is None:
        print(f"❌ 无法获取步行时长")
        return False
    
    walking_duration = walking_result.total_duration_seconds
    if walking_duration > max_walking_duration:
        print(f"❌ 步行时长{walking_duration}秒，超过{max_walking_duration}秒（{max_walking_duration // 60}分钟）")
        return False
    print(f"✅ 步行时长{walking_duration}秒，符合要求（<= {max_walking_duration}秒，即{max_walking_duration // 60}分钟）")
    
    # 步骤6: 验证时间拓扑关系（驾车时间 > 步行时间）
    print(f"\n【步骤6】验证时间拓扑关系（驾车时间 > 步行时间）")
    print("-" * 80)
    if driving_duration <= walking_duration:
        print(f"❌ 时间拓扑关系验证失败：驾车时长{driving_duration}秒 <= 步行时长{walking_duration}秒")
        print(f"   要求：驾车时长 > 步行时长")
        return False
    print(f"✅ 时间拓扑关系验证通过：驾车时长{driving_duration}秒 > 步行时长{walking_duration}秒")
    
    print(f"\n✅ 所有验证通过！")
    return True


if __name__ == "__main__":
    # 测试用例
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python 607.py <poi_id> [user_location] [bank_location]")
        print("示例: python 607.py B020402B75")
        print("示例: python 607.py B020402B75 117.200842,34.210638")
        print("示例: python 607.py B020402B75 117.200842,34.210638 117.194026,34.210794")
        print("未传参，使用示例默认值运行。")
        poi_id = "B020402B75"
        user_location = "117.200842,34.210638"
        bank_location = "117.194026,34.210794"
    else:
        poi_id = sys.argv[1]
        user_location = sys.argv[2] if len(sys.argv) > 2 else "117.200842,34.210638"
        bank_location = sys.argv[3] if len(sys.argv) > 3 else None
        

    print(f"开始验证POI: {poi_id}")
    print(f"用户坐标: {user_location}")
    if bank_location:
        print(f"银行坐标: {bank_location}")
    print("=" * 80)
    
    result = verify_poi(poi_id, user_location=user_location, bank_location=bank_location)
    
    print("=" * 80)
    print(f"验证结果: {'通过' if result else '失败'}")
