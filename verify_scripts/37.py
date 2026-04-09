"""
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
🔍 验证方法 (verification_method):

1) 周边可达性(2公里内)：调用 maps_around_search(location="123.238687,41.271614", radius="2000", keywords="洗衣店")，验证返回pois中包含 target_poi_id=B0GK3CTQ55。  
2) 获取POI坐标：调用 maps_search_detail(id="B0GK3CTQ55")，读取其 location=123.235224,41.259614。  
3) 步行时长<=20分钟：调用 maps_walking_by_coordinates(origin="123.238687,41.271614", destination="123.235224,41.259614")，验证 total_duration_seconds<=1200。  
4) 驾车时长<=5分钟：调用 maps_driving_by_coordinates(origin="123.238687,41.271614", destination="123.235224,41.259614")，验证 total_duration_seconds<=300。  
5) 直线距离<=1.5公里：调用 maps_distance(origins="123.238687,41.271614", destination="123.235224,41.259614")，验证返回distance<=1500(米)。
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
    maps_distance
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str,
    user_location: str = "123.238687,41.271614",
    search_radius: int = 2000,  # 2km
    keywords: str = "洗衣店",
    max_walking_duration: int = 20 * 60,  # 20分钟 = 1200秒
    max_driving_duration: int = 5 * 60,  # 5分钟 = 300秒
    max_distance_meters: int = 1500  # 1.5公里 = 1500米
) -> bool:
    """
    验证POI是否符合要求
    
    验证步骤：
    1) 周边可达性(2公里内)：调用 maps_around_search，验证返回pois中包含目标poi_id。
    2) 获取POI坐标：调用 maps_search_detail，读取其 location。
    3) 步行时长<=20分钟：调用 maps_walking_by_coordinates，验证 total_duration_seconds <= 1200。
    4) 驾车时长<=5分钟：调用 maps_driving_by_coordinates，验证 total_duration_seconds <= 300。
    5) 直线距离<=1.5公里：调用 maps_distance，验证返回distance <= 1500(米)。
    
    Args:
        poi_id: POI ID
        user_location: 用户坐标，格式为"经度,纬度"，默认"123.238687,41.271614"
        search_radius: 搜索半径（米），默认2000（2公里）
        keywords: 搜索关键词，默认"洗衣店"
        max_walking_duration: 最大步行时长（秒），默认1200（20分钟）
        max_driving_duration: 最大驾车时长（秒），默认300（5分钟）
        max_distance_meters: 最大直线距离（米），默认1500（1.5公里）
    
    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 周边可达性(2公里内) - 验证POI在用户周边2km内
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
    
    # 步骤2: 获取POI坐标
    poi_detail = maps_search_detail(id=poi_id)
    if poi_detail.error:
        print(f"❌ 获取POI详情失败: {poi_detail.error}")
        return False
    
    if not poi_detail.location:
        print(f"❌ POI没有location信息")
        return False
    
    poi_location = poi_detail.location
    print(f"✅ 获取POI坐标: {poi_location}")
    
    # 步骤3: 步行时长<=20分钟 - 验证步行时长不超过20分钟
    walking_result = maps_walking_by_coordinates(origin=user_location, destination=poi_location)
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
    
    # 步骤4: 驾车时长<=5分钟 - 验证驾车时长不超过5分钟
    driving_result = maps_driving_by_coordinates(origin=user_location, destination=poi_location)
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
    
    # 步骤5: 直线距离<=1.5公里 - 验证直线距离不超过1.5公里
    distance_result = maps_distance(origins=user_location, destination=poi_location)
    if distance_result.error:
        print(f"❌ 计算直线距离失败: {distance_result.error}")
        return False
    
    if not distance_result.results or len(distance_result.results) == 0:
        print(f"❌ 无法获取距离信息")
        return False
    
    # 获取第一条结果的距离
    distance_meters = distance_result.results[0].distance_meters
    if distance_meters > max_distance_meters:
        print(f"❌ 直线距离{distance_meters}米，超过{max_distance_meters}米（{max_distance_meters / 1000}公里）")
        return False
    print(f"✅ 直线距离{distance_meters}米，符合要求（<= {max_distance_meters}米，即{max_distance_meters / 1000}公里）")
    
    print(f"✅ 所有验证通过！")
    return True


if __name__ == "__main__":
    # 测试用例
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python id_562.py <poi_id> [user_location]")
        print("示例: python id_562.py B0GK3CTQ55")
        print("示例: python id_562.py B0GK3CTQ55 123.238687,41.271614")
        print("未传参，使用示例默认值运行。")
        poi_id = "B0GK3CTQ55"
        user_location = "123.238687,41.271614"
    else:
        poi_id = sys.argv[1]
        user_location = sys.argv[2] if len(sys.argv) > 2 else "123.238687,41.271614"
        

    print(f"开始验证POI: {poi_id}")
    print(f"用户坐标: {user_location}")
    print("-" * 80)
    
    result = verify_poi(poi_id, user_location=user_location)
    
    print("-" * 80)
    print(f"验证结果: {'通过' if result else '失败'}")
