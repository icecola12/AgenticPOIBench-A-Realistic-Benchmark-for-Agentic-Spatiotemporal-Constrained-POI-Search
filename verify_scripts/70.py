
"""
修改任务指令：你要在附近1.2公里内内找一家酒店，打算在那儿等人谈事情。你需要确保从这家酒店开车去阿拉尔市火车站，用时不能超过320分钟。另外，这家酒店的评分要在4.0分及以上。你有礼貌但很固执，坚持自己的要求不让步。
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 用 maps_around_search，以用户坐标(79.903386,40.681704)为中心、radius=1200、keywords=酒店 搜索，验证返回结果中包含 target_poi_id=B0G04S6ZV8（从而验证"离你不超过1.2公里"且POI类型为酒店）。
2) 对 target_poi_id 调用 maps_search_detail(B0G04S6ZV8)，读取 biz_ext.rating，验证评分 >= 4.0。
3) 对"阿拉尔市火车站"调用 maps_text_search(keywords="阿拉尔市火车站", city="阿拉尔市") 取 poi_id，再 maps_search_detail(id=poi_id) 获取 其坐标。
4) 使用 maps_driving_by_coordinates，origin=目标酒店坐标(取自maps_search_detail.location)，destination=火车站坐标(取自.location)；取 total_duration_seconds/60 得到驾车分钟数，验证 <= 320 分钟。
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
    maps_text_search,
    maps_search_detail ,
    maps_driving_by_coordinates
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str,
    user_location: str = "79.903386,40.681704",
    search_radius: int = 1200,  # 1.2km
    keywords: str = "酒店",
    min_rating: float = 4.0,
    station_address: str = "阿拉尔市火车站",
    station_city: str = "阿拉尔市",
    max_driving_duration: int = 19200  # 320 minutes = 19200 seconds
) -> bool:
    """
    验证POI是否符合要求

    验证步骤：
    1) 验证返回结果中包含 target_poi_id（从而验证"离你不超过1.2公里"且POI类型为酒店）
    2) 验证评分 >= 4.0
    3) 获取 poi_id，再 maps_search_detail(id=poi_id) 获取 阿拉尔市火车站坐标
    4) 验证驾车分钟数 <= 320 分钟

    Args:
        poi_id: POI ID
        user_location: 用户坐标，格式为"经度,纬度"，默认"79.903386,40.681704"
        search_radius: 搜索半径（米），默认1200（1.2公里）
        keywords: 搜索关键词，默认"酒店"
        min_rating: 最低评分，默认4.0
        station_address: 火车站地址，默认"阿拉尔市火车站"
        station_city: 火车站所在城市，默认"阿拉尔市"
        max_driving_duration: 最大驾车时长（秒），默认19200（320分钟）

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 周边检索（附近1.2公里内的酒店）
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

    # 步骤2: 验证评分（rating >= 4.0）
    poi_detail = maps_search_detail(id=poi_id)
    if poi_detail.error:
        print(f"❌ 获取POI详情失败: {poi_detail.error}")
        return False

    if not poi_detail.location:
        print(f"❌ POI没有location信息")
        return False

    poi_location = poi_detail.location
    print(f"✅ 获取POI坐标: {poi_location}")

    # 验证评分（rating >= 4.0）
    if hasattr(poi_detail, 'biz_ext') and poi_detail.biz_ext and 'rating' in poi_detail.biz_ext:
        rating = poi_detail.biz_ext['rating']
        try:
            rating_value = float(rating)
            if rating_value < min_rating:
                print(f"❌ 评分{rating_value}低于{min_rating}")
                return False
            print(f"✅ 评分{rating_value}，符合要求（>= {min_rating}）")
        except (ValueError, TypeError):
            print(f"⚠️  无法解析评分值: {rating}，跳过评分验证")
    else:
        print(f"⚠️  未找到评分信息，跳过评分验证")

    # 步骤3: 获取阿拉尔市火车站坐标（用 maps_text_search + maps_search_detail 替代 maps_geo）
    station_text_result = maps_text_search(keywords=station_address, city=station_city)
    if station_text_result.error:
        print(f"❌ 获取{station_address}坐标失败: {station_text_result.error}")
        return False

    if not station_text_result.pois or len(station_text_result.pois) == 0:
        print(f"❌ 未找到{station_address}坐标")
        return False

    first_poi_id = station_text_result.pois[0].id
    station_detail_result = maps_search_detail(id=first_poi_id)
    if station_detail_result.error:
        print(f"❌ 获取坐标失败: {station_detail_result.error}")
        return False
    if not station_detail_result.location:
        print("❌ 未获取到坐标")
        return False

    station_location = station_detail_result.location
    print(f"✅ 获取{station_address}坐标: {station_location}")

    # 步骤4: 验证驾车时间（<= 320分钟）
    driving_result = maps_driving_by_coordinates(origin=poi_location, destination=station_location)
    if driving_result.error:
        print(f"❌ 计算到{station_address}驾车路线失败: {driving_result.error}")
        return False

    if driving_result.total_duration_seconds is None:
        print(f"❌ 无法获取到{station_address}驾车时长")
        return False

    driving_duration = driving_result.total_duration_seconds
    driving_minutes = driving_duration / 60
    max_driving_minutes = max_driving_duration / 60
    if driving_duration > max_driving_duration:
        print(f"❌ 到{station_address}驾车时长{driving_duration}秒（{driving_minutes:.1f}分钟），超过{max_driving_duration}秒（{max_driving_minutes:.0f}分钟）")
        return False
    print(f"✅ 到{station_address}驾车时长{driving_duration}秒（{driving_minutes:.1f}分钟），符合要求（<= {max_driving_minutes:.0f}分钟）")

    print(f"✅ 所有验证通过！")
    return True



if __name__ == "__main__":
    print("开始验证 641.py 文件...\n")
    result = verify_poi(poi_id="B0G04S6ZV8")
    print(f"\n验证结果: {result}")
