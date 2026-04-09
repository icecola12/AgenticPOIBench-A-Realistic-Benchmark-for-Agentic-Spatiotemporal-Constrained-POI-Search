"""
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
🔍 验证方法 (verification_method):

1) 距离约束：调用 maps_around_search(location='106.075429,30.784716', radius='2000', keywords='医院')，验证返回pois中包含 target_poi_id='B033103ELP'。  
2) 获取POI坐标：调用 maps_search_detail(id='B033103ELP') 获取医院坐标 dest='106.082156,30.786585'。  
3) 骑行时间约束：调用 maps_bicycling_by_coordinates(origin='106.075429,30.784716', destination='106.082156,30.786585')，验证 total_duration_seconds ≤ 480（8分钟）。  
4) 步行-骑行时间差约束：调用 maps_walking_by_coordinates(origin='106.075429,30.784716', destination='106.082156,30.786585') 得到 t_walk；结合第3步得到 t_bike；验证 (t_walk - t_bike) ≥ 960（16分钟）。  
5) 到高铁站驾车时间约束：调用 maps_search_detail(id='B0FFG38DLA') 获取南充北站坐标 station='106.070913,30.856368'；再调用 maps_driving_by_coordinates(origin='106.082156,30.786585', destination='106.070913,30.856368')，验证 total_duration_seconds ≤ 1200（20分钟）。
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
    maps_bicycling_by_coordinates,
    maps_driving_by_coordinates
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str,
    user_location: str = "106.075429,30.784716",
    search_radius: int = 2000,  # 2km
    keywords: str = "医院",
    max_bicycling_duration: int = 8 * 60,  # 8分钟 = 480秒
    min_walking_bicycling_diff: int = 16 * 60,  # 16分钟 = 960秒
    station_poi_id: str = "B0FFG38DLA",  # 南充北站POI ID
    max_driving_duration: int = 20 * 60  # 20分钟 = 1200秒
) -> bool:
    """
    验证POI是否符合要求
    
    验证步骤：
    1) 距离约束：调用 maps_around_search，验证返回pois中包含目标poi_id。
    2) 获取POI坐标：调用 maps_search_detail 获取医院坐标。
    3) 骑行时间约束：调用 maps_bicycling_by_coordinates，验证 total_duration_seconds ≤ 480（8分钟）。
    4) 步行-骑行时间差约束：调用 maps_walking_by_coordinates 得到 t_walk；结合第3步得到 t_bike；验证 (t_walk - t_bike) ≥ 960（16分钟）。
    5) 到高铁站驾车时间约束：调用 maps_search_detail 获取南充北站坐标；再调用 maps_driving_by_coordinates，验证 total_duration_seconds ≤ 1200（20分钟）。
    
    Args:
        poi_id: POI ID
        user_location: 用户坐标，格式为"经度,纬度"，默认"106.075429,30.784716"
        search_radius: 搜索半径（米），默认2000（2公里）
        keywords: 搜索关键词，默认"医院"
        max_bicycling_duration: 最大骑行时长（秒），默认480（8分钟）
        min_walking_bicycling_diff: 最小步行-骑行时间差（秒），默认960（16分钟）
        station_poi_id: 高铁站POI ID，默认"B0FFG38DLA"（南充北站）
        max_driving_duration: 最大驾车时长（秒），默认1200（20分钟）
    
    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 距离约束 - 验证POI在用户周边2km内
    around_search_result = maps_around_search(
        location=user_location,
        radius=str(search_radius),
        keywords=keywords
    )
    if around_search_result.error:
        print(f"❌ 搜索周边POI失败: {around_search_result.error}")
        return False
    
    if not around_search_result.pois or len(around_search_result.pois) == 0:
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
    
    # 步骤2: 获取目标POI坐标
    poi_detail = maps_search_detail(id=poi_id)
    if poi_detail.error:
        print(f"❌ 获取POI详情失败: {poi_detail.error}")
        return False
    
    if not poi_detail.location:
        print(f"❌ POI没有location信息")
        return False
    
    poi_location = poi_detail.location
    print(f"✅ 获取POI坐标: {poi_location}")
    
    # 步骤3: 骑行时间约束 - 验证骑行时长不超过8分钟
    bicycling_result = maps_bicycling_by_coordinates(origin=user_location, destination=poi_location)
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
    
    # 步骤4: 步行-骑行时间差约束 - 验证步行时间比骑行时间至少慢16分钟
    walking_result = maps_walking_by_coordinates(origin=user_location, destination=poi_location)
    if walking_result.error:
        print(f"❌ 计算步行路线失败: {walking_result.error}")
        return False
    
    if walking_result.total_duration_seconds is None:
        print(f"❌ 无法获取步行时长")
        return False
    
    walking_duration = walking_result.total_duration_seconds
    time_diff = walking_duration - bicycling_duration
    
    if time_diff < min_walking_bicycling_diff:
        print(f"❌ 步行-骑行时间差{time_diff}秒，小于{min_walking_bicycling_diff}秒（{min_walking_bicycling_diff // 60}分钟）")
        print(f"   步行时长: {walking_duration}秒（{walking_duration // 60}分钟）")
        print(f"   骑行时长: {bicycling_duration}秒（{bicycling_duration // 60}分钟）")
        return False
    print(f"✅ 步行-骑行时间差{time_diff}秒，符合要求（>= {min_walking_bicycling_diff}秒，即{min_walking_bicycling_diff // 60}分钟）")
    print(f"   步行时长: {walking_duration}秒（{walking_duration // 60}分钟）")
    print(f"   骑行时长: {bicycling_duration}秒（{bicycling_duration // 60}分钟）")
    
    # 步骤5: 到高铁站驾车时间约束 - 验证从医院到南充北站驾车时间不超过20分钟
    station_detail = maps_search_detail(id=station_poi_id)
    if station_detail.error:
        print(f"❌ 获取高铁站详情失败: {station_detail.error}")
        return False
    
    if not station_detail.location:
        print(f"❌ 高铁站没有location信息")
        return False
    
    station_location = station_detail.location
    print(f"✅ 获取高铁站坐标: {station_location} ({station_detail.name})")
    
    driving_result = maps_driving_by_coordinates(origin=poi_location, destination=station_location)
    if driving_result.error:
        print(f"❌ 计算驾车路线失败: {driving_result.error}")
        return False
    
    if driving_result.total_duration_seconds is None:
        print(f"❌ 无法获取驾车时长")
        return False
    
    driving_duration = driving_result.total_duration_seconds
    if driving_duration > max_driving_duration:
        print(f"❌ 到高铁站驾车时长{driving_duration}秒，超过{max_driving_duration}秒（{max_driving_duration // 60}分钟）")
        return False
    print(f"✅ 到高铁站驾车时长{driving_duration}秒，符合要求（<= {max_driving_duration}秒，即{max_driving_duration // 60}分钟）")
    
    print(f"✅ 所有验证通过！")
    return True


if __name__ == "__main__":
    # 测试用例
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python id_544.py <poi_id> [user_location] [station_poi_id]")
        print("示例: python id_544.py B033103ELP")
        print("示例: python id_544.py B033103ELP 106.075429,30.784716")
        print("示例: python id_544.py B033103ELP 106.075429,30.784716 B0FFG38DLA")
        print("未传参，使用示例默认值运行。")
        poi_id = "B033103ELP"
        user_location = "106.075429,30.784716"
        station_poi_id = "B0FFG38DLA"
    else:
        poi_id = sys.argv[1]
        user_location = sys.argv[2] if len(sys.argv) > 2 else "106.075429,30.784716"
        station_poi_id = sys.argv[3] if len(sys.argv) > 3 else "B0FFG38DLA"
        

    print(f"开始验证POI: {poi_id}")
    print(f"用户坐标: {user_location}")
    print(f"高铁站POI ID: {station_poi_id}")
    print("-" * 80)
    
    result = verify_poi(poi_id, user_location=user_location, station_poi_id=station_poi_id)
    
    print("-" * 80)
    print(f"验证结果: {'通过' if result else '失败'}")
