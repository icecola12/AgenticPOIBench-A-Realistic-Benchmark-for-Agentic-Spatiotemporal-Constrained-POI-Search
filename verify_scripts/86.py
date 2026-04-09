"""
修改任务指令：你想找一个附近2km内的商场。为了等会儿赶去北京西站，你希望从这个商场打车过去不超过12分钟。另外你不想去评分太一般的地方，所以这个商场的评分要在4.8分及以上。你"自信、有条理、有创造力，但没有耐心。"
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 半径约束验证：调用 maps_around_search(location='116.364468,39.914911', radius='2000', keywords='商场')，检查返回pois中包含目标POI id=B000A62FA1（验证"附近2km内的商场"）。  
2) 评分约束验证：调用 maps_search_detail(id='B000A62FA1')，读取 biz_ext.rating，验证 rating >= 4.8。  
3) 获取北京西站坐标：调用 maps_geo(address='北京西站', city='北京')，取返回 results[0].location 作为西站坐标。  
4) 打车时间（用驾车时长近似）约束验证：用步骤2得到的商场坐标location，调用 maps_driving_by_coordinates(origin=商场location, destination=北京西站location)，读取 total_duration_seconds，验证 total_duration_seconds <= 12*60。
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
    maps_driving_by_coordinates,
    maps_geo,
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str,
    user_location: str = "116.364468,39.914911",
    mall_location: str = None,
    search_radius: int = 2000,
    keywords: str = "商场",
    min_rating: float = 4.8,
    station_address: str = "北京西站",
    station_city: str = "北京",
    station_location: str = None,
    max_driving_duration: int = 720,  # 12分钟 = 720秒
) -> bool:
    """
    验证POI是否符合要求
    
    验证步骤：
    1) 半径约束验证：调用 maps_around_search，检查返回pois中包含目标POI id（验证"附近2km内的商场"）。
    2) 评分约束验证：调用 maps_search_detail，读取 biz_ext.rating，验证 rating >= 4.8。
    3) 获取北京西站坐标：调用 maps_geo，取返回 results[0].location 作为西站坐标。
    4) 打车时间（用驾车时长近似）约束验证：用步骤2得到的商场坐标location，调用 maps_driving_by_coordinates，读取 total_duration_seconds，验证 total_duration_seconds <= 12*60。
    
    Args:
        poi_id: 目标商场 POI ID，默认应为 "B000A62FA1"
        user_location: 用户坐标，格式为"经度,纬度"，默认"116.364468,39.914911"
        mall_location: 商场坐标，格式为"经度,纬度"，如果为None则从POI详情中获取
        search_radius: 搜索半径（米），默认2000（2公里）
        keywords: 搜索关键词，默认"商场"
        min_rating: 最小评分，默认4.8
        station_address: 北京西站地址，默认"北京西站"
        station_city: 北京西站所在城市，默认"北京"
        station_location: 北京西站坐标，格式为"经度,纬度"，如果为None则从maps_geo获取
        max_driving_duration: 到北京西站最大驾车时长（秒），默认720（12分钟）
    
    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 半径约束验证
    print(f"【步骤1】验证半径约束（{search_radius}米范围内，关键词：{keywords}）")
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
    
    # 步骤2: 评分约束验证
    print(f"\n【步骤2】验证评分约束（评分>={min_rating}）")
    print("-" * 80)
    mall_detail = maps_search_detail(id=poi_id)
    if mall_detail.error:
        print(f"❌ 获取商场详情失败: {mall_detail.error}")
        return False
    
    # 获取商场坐标
    if mall_detail.location:
        mall_location = mall_detail.location
        print(f"✅ 获取商场坐标: {mall_location} ({mall_detail.name})")
    else:
        if mall_location is None:
            print(f"❌ POI没有location信息")
            return False
        print(f"⚠️  商场详情中没有location信息，使用传入的默认坐标: {mall_location}")
    
    # 验证评分
    if not mall_detail.biz_ext:
        print(f"❌ POI没有biz_ext信息")
        return False
    
    rating = mall_detail.biz_ext.get("rating")
    if rating is None:
        print(f"❌ POI没有rating信息")
        return False
    
    try:
        rating_value = float(rating)
    except (ValueError, TypeError):
        print(f"❌ 无法解析rating值: {rating}")
        return False
    
    if rating_value < min_rating:
        print(f"❌ POI评分{rating_value}，低于要求的最小评分{min_rating}")
        return False
    print(f"✅ POI评分{rating_value}，满足要求（>={min_rating}）")
    
    # 步骤3: 获取北京西站坐标
    print(f"\n【步骤3】获取北京西站坐标")
    print("-" * 80)
    geo_result = maps_geo(address=station_address, city=station_city)
    if geo_result.error:
        print(f"❌ 获取北京西站坐标失败: {geo_result.error}")
        return False
    
    if not geo_result.results or len(geo_result.results) == 0:
        print(f"❌ 未找到北京西站坐标")
        return False
    
    if station_location is None:
        station_location = geo_result.results[0].location
    print(f"✅ 获取北京西站坐标: {station_location} ({station_address})")
    
    # 步骤4: 打车时间（用驾车时长近似）约束验证
    print(f"\n【步骤4】验证打车时间约束（用驾车时长近似，<={max_driving_duration}秒，即{max_driving_duration // 60}分钟）")
    print("-" * 80)
    driving_result = maps_driving_by_coordinates(
        origin=mall_location,
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
    
    print(f"\n✅ 所有验证通过！")
    return True


if __name__ == "__main__":
    # 测试用例
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python 676.py <poi_id> [user_location]")
        print("示例: python 676.py B000A62FA1")
        print("示例: python 676.py B000A62FA1 116.364468,39.914911")
        print("未传参，使用示例默认值运行。")
        poi_id = "B000A62FA1"
        user_location = "116.364468,39.914911"
    else:
        poi_id = sys.argv[1]
        user_location = sys.argv[2] if len(sys.argv) > 2 else "116.364468,39.914911"
        

    print(f"开始验证POI: {poi_id}")
    print(f"用户坐标: {user_location}")
    print("=" * 80)
    
    result = verify_poi(poi_id, user_location=user_location)
    
    print("=" * 80)
    print(f"验证结果: {'通过' if result else '失败'}")
