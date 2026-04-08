"""
修改任务指令：你想在附近2公里内找一家医院，骑车过去不超过8分钟，而且步行过去也别超过25分钟。因为还要尽快转乘地铁，所以这家医院到平安里地铁站的直线距离得在500米以内，并且从医院步行到平安里地铁站也要控制在25分钟内。你情绪化，时而冷静时而愤怒，态度变化快。
# 注意：首个约束已修正为"你想在附近2公里内找一家医院"（强调"附近指定距离内"，而非"不超过指定距离"）

根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 调用 maps_around_search(location='116.365003,39.929376', radius='2000', keywords='医院')，验证返回pois中包含目标poi_id=B000A8UMY0。  
2) 调用 maps_search_detail(id='B000A8UMY0') 获取目标POI的location。  
3) 调用 maps_bicycling_by_coordinates(origin='116.365003,39.929376', destination=目标POI.location)，验证 total_duration_seconds<=480（8分钟）。  
4) 调用 maps_walking_by_coordinates(origin='116.365003,39.929376', destination=目标POI.location)，验证 total_duration_seconds<=1500（25分钟）。  
5) 调用 maps_geo(address='平安里地铁站', city='北京') 获取地铁站location_s。  
6) 调用 maps_distance(origins=目标POI.location, destination=location_s)，验证 distance_meters<=500。  
7) 调用 maps_walking_by_coordinates(origin=目标POI.location, destination=location_s)，验证 total_duration_seconds<=1500（25分钟）。
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
    maps_bicycling_by_coordinates,
    maps_walking_by_coordinates,
    maps_geo,
    maps_distance
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str,
    user_location: str = "116.365003,39.929376",
    hospital_location: str = None,
    search_radius: int = 2000,
    keywords: str = "医院",
    max_bicycling_duration: int = 480,  # 8分钟 = 480秒
    max_walking_duration: int = 1500,  # 25分钟 = 1500秒
    subway_address: str = "平安里地铁站",
    subway_city: str = "北京",
    subway_location: str = None,
    max_distance_meters: int = 500,
    max_walking_to_subway_duration: int = 1500  # 25分钟 = 1500秒
) -> bool:
    """
    验证POI是否符合要求
    
    验证步骤：
    1) 调用 maps_around_search，验证返回pois中包含目标poi_id。
    2) 调用 maps_search_detail 获取目标POI的location。
    3) 调用 maps_bicycling_by_coordinates，验证 total_duration_seconds <= 480（8分钟）。
    4) 调用 maps_walking_by_coordinates，验证 total_duration_seconds <= 1500（25分钟）。
    5) 调用 maps_geo 获取地铁站location。
    6) 调用 maps_distance，验证 distance_meters <= 500。
    7) 调用 maps_walking_by_coordinates，验证 total_duration_seconds <= 1500（25分钟）。
    
    Args:
        poi_id: POI ID，默认"B000A8UMY0"
        user_location: 用户坐标，格式为"经度,纬度"，默认"116.365003,39.929376"
        hospital_location: 医院坐标，格式为"经度,纬度"，如果为None则从POI详情中获取
        search_radius: 搜索半径（米），默认2000（2公里）
        keywords: 搜索关键词，默认"医院"
        max_bicycling_duration: 最大骑行时长（秒），默认480（8分钟）
        max_walking_duration: 最大步行时长（秒），默认1500（25分钟）
        subway_address: 地铁站地址，默认"平安里地铁站"
        subway_city: 地铁站所在城市，默认"北京"
        subway_location: 地铁站坐标，格式为"经度,纬度"，如果为None则从maps_geo获取
        max_distance_meters: 最大直线距离（米），默认500
        max_walking_to_subway_duration: 到医院到地铁站最大步行时长（秒），默认1500（25分钟）
    
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
    hospital_detail = maps_search_detail(id=poi_id)
    if hospital_detail.error:
        print(f"❌ 获取医院详情失败: {hospital_detail.error}")
        return False
    
    if hospital_detail.location:
        hospital_location = hospital_detail.location
        print(f"✅ 获取医院坐标: {hospital_location} ({hospital_detail.name})")
    else:
        if hospital_location is None:
            print(f"❌ POI没有location信息")
            return False
        print(f"⚠️  医院详情中没有location信息，使用传入的默认坐标: {hospital_location}")
    
    # 步骤3: 骑行时间约束
    print(f"\n【步骤3】验证骑行时间约束（<={max_bicycling_duration}秒，即{max_bicycling_duration // 60}分钟）")
    print("-" * 80)
    bicycling_result = maps_bicycling_by_coordinates(
        origin=user_location,
        destination=hospital_location
    )
    if bicycling_result.error:
        print(f"❌ 计算骑行路线失败: {bicycling_result.error}")
        return False
    
    if bicycling_result.total_duration_seconds is None:
        print(f"❌ 无法获取骑行时长")
        return False
    
    bicycling_duration = bicycling_result.total_duration_seconds
    if bicycling_duration > max_bicycling_duration:
        print(f"❌ 骑行时长{bicycling_duration}秒，超过{max_bicycling_duration}秒（{max_bicycling_duration // 60}分钟）")
        return False
    print(f"✅ 骑行时长{bicycling_duration}秒，符合要求（<= {max_bicycling_duration}秒，即{max_bicycling_duration // 60}分钟）")
    
    # 步骤4: 步行时间约束
    print(f"\n【步骤4】验证步行时间约束（<={max_walking_duration}秒，即{max_walking_duration // 60}分钟）")
    print("-" * 80)
    walking_result = maps_walking_by_coordinates(
        origin=user_location,
        destination=hospital_location
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
    
    # 步骤5: 获取地铁站坐标
    print(f"\n【步骤5】获取地铁站坐标")
    print("-" * 80)
    geo_result = maps_geo(address=subway_address, city=subway_city)
    if geo_result.error:
        print(f"❌ 获取地铁站坐标失败: {geo_result.error}")
        return False
    
    if not geo_result.results or len(geo_result.results) == 0:
        print(f"❌ 未找到地铁站坐标")
        return False
    
    subway_location = geo_result.results[0].location
    print(f"✅ 获取地铁站坐标: {subway_location} ({subway_address})")
    
    # 步骤6: 直线距离约束
    print(f"\n【步骤6】验证直线距离约束（<={max_distance_meters}米）")
    print("-" * 80)
    distance_result = maps_distance(
        origins=hospital_location,
        destination=subway_location
    )
    if distance_result.error:
        print(f"❌ 计算直线距离失败: {distance_result.error}")
        return False
    
    if not distance_result.results or len(distance_result.results) == 0:
        print(f"❌ 无法获取距离信息")
        return False
    
    distance_meters = distance_result.results[0].distance_meters
    if distance_meters > max_distance_meters:
        print(f"❌ 直线距离{distance_meters}米，超过{max_distance_meters}米")
        return False
    print(f"✅ 直线距离{distance_meters}米，符合要求（<= {max_distance_meters}米）")
    
    # 步骤7: 医院到地铁站步行时间约束
    print(f"\n【步骤7】验证医院到地铁站步行时间约束（<={max_walking_to_subway_duration}秒，即{max_walking_to_subway_duration // 60}分钟）")
    print("-" * 80)
    walking_to_subway_result = maps_walking_by_coordinates(
        origin=hospital_location,
        destination=subway_location
    )
    if walking_to_subway_result.error:
        print(f"❌ 计算步行路线失败: {walking_to_subway_result.error}")
        return False
    
    if walking_to_subway_result.total_duration_seconds is None:
        print(f"❌ 无法获取步行时长")
        return False
    
    walking_to_subway_duration = walking_to_subway_result.total_duration_seconds
    if walking_to_subway_duration > max_walking_to_subway_duration:
        print(f"❌ 步行时长{walking_to_subway_duration}秒，超过{max_walking_to_subway_duration}秒（{max_walking_to_subway_duration // 60}分钟）")
        return False
    print(f"✅ 步行时长{walking_to_subway_duration}秒，符合要求（<= {max_walking_to_subway_duration}秒，即{max_walking_to_subway_duration // 60}分钟）")
    
    print(f"\n✅ 所有验证通过！")
    return True


if __name__ == "__main__":
    # 测试用例
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python 604.py <poi_id> [user_location] [hospital_location]")
        print("示例: python 604.py B000A8UMY0")
        print("示例: python 604.py B000A8UMY0 116.365003,39.929376")
        print("示例: python 604.py B000A8UMY0 116.365003,39.929376 116.365003,39.929376")
        print("未传参，使用示例默认值运行。")
        poi_id = "B000A8UMY0"
        user_location = "116.365003,39.929376"
    else:
        poi_id = sys.argv[1]
        user_location = sys.argv[2] if len(sys.argv) > 2 else "116.365003,39.929376"
        hospital_location = sys.argv[3] if len(sys.argv) > 3 else None
        

    print(f"开始验证POI: {poi_id}")
    print(f"用户坐标: {user_location}")
    if hospital_location:
        print(f"医院坐标: {hospital_location}")
    print("=" * 80)
    
    result = verify_poi(poi_id, user_location=user_location, hospital_location=hospital_location)
    
    print("=" * 80)
    print(f"验证结果: {'通过' if result else '失败'}")
