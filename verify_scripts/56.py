
"""
修改任务指令：你想在你附近找一家离你不超过2公里的洗衣店。因为你等会儿要去赶高铁，所以从洗衣店打车到郑州东站，路上用时得控制在20分钟以内。另外你希望这家洗衣店口碑好一点，评分至少要到3.8分。为了取件更方便，你还想要洗衣店步行到最近的地铁站不超过1公里。你健忘，且沟通时会随机出现拼写错误。
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 周边范围验证：调用 maps_around_search(location="113.649811,34.782476", radius="2000", keywords="洗衣")，验证返回pois中包含 target_poi_id=B0KKXSPGNW。
2) POI评分验证：调用 maps_search_detail(id="B0KKXSPGNW")，读取 biz_ext.rating，验证 rating >= 3.8,并获得该POI的location。
3) 车程到高铁站验证：调用 maps_search_detail(id="B017316LOP") 获取"郑州东站"的location=113.779558,34.759081；再调用 maps_driving_by_coordinates(origin=<洗衣店location>, destination=<郑州东站location>)，验证 total_duration_seconds <= 1200。
4) 地铁站邻近验证：以洗衣店location为中心调用 maps_around_search(location=<洗衣店location>, radius="1000", keywords="地铁站")，验证返回pois不为空（存在至少一个地铁站POI落在1公里内）。
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
    maps_driving_by_coordinates
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str,
    user_location: str = "113.649811,34.782476",
    search_radius: int = 2000,  # 2km
    keywords: str = "洗衣",
    min_rating: float = 3.8,
    station_id: str = "B017316LOP",  # 郑州东站
    max_driving_duration: int = 1200,  # 20 minutes = 1200 seconds
    metro_search_radius: int = 1000,  # 1km
    metro_keywords: str = "地铁站"
) -> bool:
    """
    验证POI是否符合要求

    验证步骤：
    1) 周边范围验证：验证返回pois中包含 target_poi_id
    2) POI评分验证：验证 rating >= 3.8，并获得该POI的location
    3) 车程到高铁站验证：验证 total_duration_seconds <= 1200
    4) 地铁站邻近验证：验证返回pois不为空

    Args:
        poi_id: POI ID
        user_location: 用户坐标，格式为"经度,纬度"，默认"113.649811,34.782476"
        search_radius: 搜索半径（米），默认2000（2公里）
        keywords: 搜索关键词，默认"洗衣"
        min_rating: 最低评分，默认3.8
        station_id: 高铁站POI ID，默认"B017316LOP"（郑州东站）
        max_driving_duration: 最大驾车时长（秒），默认1200（20分钟）
        metro_search_radius: 地铁站搜索半径（米），默认1000（1公里）
        metro_keywords: 地铁站搜索关键词，默认"地铁站"

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 周边范围验证（附近2公里内的洗衣店）
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

    # 步骤2: POI评分验证
    poi_detail = maps_search_detail(id=poi_id)
    if poi_detail.error:
        print(f"❌ 获取POI详情失败: {poi_detail.error}")
        return False

    if not poi_detail.location:
        print(f"❌ POI没有location信息")
        return False

    poi_location = poi_detail.location
    print(f"✅ 获取POI坐标: {poi_location}")

    # 验证评分（rating >= 3.8）
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

    # 步骤3: 车程到高铁站验证
    # 获取郑州东站坐标
    station_detail = maps_search_detail(id=station_id)
    if station_detail.error:
        print(f"❌ 获取高铁站详情失败: {station_detail.error}")
        return False

    if not station_detail.location:
        print(f"❌ 高铁站没有location信息")
        return False

    station_location = station_detail.location
    print(f"✅ 获取郑州东站坐标: {station_location}")

    # 验证驾车时间（<= 20分钟）
    driving_result = maps_driving_by_coordinates(origin=poi_location, destination=station_location)
    if driving_result.error:
        print(f"❌ 计算到郑州东站驾车路线失败: {driving_result.error}")
        return False

    if driving_result.total_duration_seconds is None:
        print(f"❌ 无法获取到郑州东站驾车时长")
        return False

    driving_duration = driving_result.total_duration_seconds
    if driving_duration > max_driving_duration:
        print(f"❌ 到郑州东站驾车时长{driving_duration}秒，超过{max_driving_duration}秒（{max_driving_duration // 60}分钟）")
        return False
    print(f"✅ 到郑州东站驾车时长{driving_duration}秒，符合要求（<= {max_driving_duration}秒，即{max_driving_duration // 60}分钟）")

    # 步骤4: 地铁站邻近验证（1公里内有地铁站）
    metro_search_result = maps_around_search(
        location=poi_location,
        radius=str(metro_search_radius),
        keywords=metro_keywords
    )
    if metro_search_result.error:
        print(f"❌ 搜索周边地铁站失败: {metro_search_result.error}")
        return False

    if not metro_search_result.pois or len(metro_search_result.pois) == 0:
        print(f"❌ {metro_search_radius}米范围内未找到地铁站")
        return False

    metro_count = len(metro_search_result.pois)
    print(f"✅ {metro_search_radius}米范围内找到{metro_count}个地铁站，符合要求")

    print(f"✅ 所有验证通过！")
    return True



if __name__ == "__main__":
    print("开始验证 614.py 文件...\n")
    result = verify_poi(poi_id="B0KKXSPGNW")
    print(f"\n验证结果: {result}")
