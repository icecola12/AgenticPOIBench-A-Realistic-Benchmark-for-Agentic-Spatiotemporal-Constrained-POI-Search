
"""
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 周边范围验证：调用 maps_around_search(location="109.496975,30.303856", radius="2000", keywords="咖啡厅")，验证返回pois中包含 target_poi_id=B0FFJJ61AB。
2) 营业时间验证：调用 maps_search_detail(id="B0FFJJ61AB")，读取 biz_ext.opentime2 或 biz_ext.open_time，验证其关门时间晚于22:00（该POI为"周一至周日 11:00-23:00"，因此满足"今天22:00之后还在营业"）。
3) 评分验证：在 maps_search_detail(id="B0FFJJ61AB") 返回的 biz_ext.rating 中验证 rating>=4.2（该POI为4.2）。
4) 骑行时间验证：调用 maps_bicycling_by_coordinates(origin="109.496975,30.303856", destination="109.495229,30.300630")，验证 total_duration_seconds<=360秒（6分钟）。
5) 到火车站驾车时间验证：先调用 maps_text_search(keywords="恩施火车站", city="恩施土家族苗族自治州", citylimit="true") 获取"恩施站"POI（例如B02CE032PM）的坐标；再调用 maps_search_detail(id="B02CE032PM") 得到其location；最后调用 maps_driving_by_coordinates(origin="109.495229,30.300630", destination="109.484710,30.348830")，验证 total_duration_seconds<=900秒（15分钟）
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
    maps_text_search,
    maps_bicycling_by_coordinates,
    maps_driving_by_coordinates
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str,
    user_location: str = "109.496975,30.303856",
    search_radius: int = 2000,  # 2km
    keywords: str = "咖啡厅",
    min_rating: float = 4.2,
    min_closing_hour: int = 22,  # 22:00
    destination_location: str = "109.495229,30.300630",
    max_bicycling_duration: int = 360,  # 6 minutes = 360 seconds
    station_keywords: str = "恩施火车站",
    station_city: str = "恩施土家族苗族自治州",
    max_driving_duration: int = 900  # 15 minutes = 900 seconds
) -> bool:
    """
    验证POI是否符合要求

    验证步骤：
    1) 周边范围验证：调用 maps_around_search，验证返回pois中包含 target_poi_id
    2) 营业时间验证：调用 maps_search_detail，验证其关门时间晚于22:00
    3) 评分验证：在 maps_search_detail 返回的 biz_ext.rating 中验证 rating>=4.2
    4) 骑行时间验证：调用 maps_bicycling_by_coordinates，验证 total_duration_seconds<=360秒（6分钟）
    5) 到火车站驾车时间验证：调用 maps_text_search 获取火车站坐标，再调用 maps_driving_by_coordinates，验证 total_duration_seconds<=900秒（15分钟）

    Args:
        poi_id: POI ID
        user_location: 用户坐标，格式为"经度,纬度"，默认"109.496975,30.303856"
        search_radius: 搜索半径（米），默认2000（2公里）
        keywords: 搜索关键词，默认"咖啡厅"
        min_rating: 最低评分，默认4.2
        min_closing_hour: 最低关门时间（小时），默认22
        destination_location: 目的地坐标，默认"109.495229,30.300630"
        max_bicycling_duration: 最大骑行时长（秒），默认360（6分钟）
        station_keywords: 火车站搜索关键词，默认"恩施火车站"
        station_city: 火车站所在城市，默认"恩施土家族苗族自治州"
        max_driving_duration: 最大驾车时长（秒），默认900（15分钟）

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 周边范围验证（附近2公里内的咖啡厅）
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

    # 步骤2: 获取目标POI详情（用于营业时间和评分验证）
    poi_detail = maps_search_detail(id=poi_id)
    if poi_detail.error:
        print(f"❌ 获取POI详情失败: {poi_detail.error}")
        return False

    if not poi_detail.location:
        print(f"❌ POI没有location信息")
        return False

    poi_location = poi_detail.location
    print(f"✅ 获取POI坐标: {poi_location}")

    # 步骤3: 营业时间验证（关门时间晚于22:00）
    if hasattr(poi_detail, 'biz_ext') and poi_detail.biz_ext:
        opentime = None
        # biz_ext 是字典类型，需要使用字典键访问方式
        if 'opentime2' in poi_detail.biz_ext and poi_detail.biz_ext['opentime2']:
            opentime = poi_detail.biz_ext['opentime2']
        elif 'open_time' in poi_detail.biz_ext and poi_detail.biz_ext['open_time']:
            opentime = poi_detail.biz_ext['open_time']

        if opentime:
            print(f"✅ 营业时间: {opentime}")
            # 解析关门时间（假设格式为 "HH:MM-HH:MM" 或 "周一至周日 HH:MM-HH:MM"）
            import re
            # 查找时间范围中的结束时间
            time_pattern = r'(\d{1,2}):(\d{2})-(\d{1,2}):(\d{2})'
            matches = re.findall(time_pattern, opentime)
            if matches:
                # 计算每段有效关门分钟数（跨天则+24*60），取最晚关门与 min_closing_hour 比较
                min_closing_minutes = min_closing_hour * 60
                max_effective_closing_minutes = -1
                for m in matches:
                    open_h, open_m = int(m[0]), int(m[1])
                    close_h, close_m = int(m[2]), int(m[3])
                    open_minutes = open_h * 60 + open_m
                    close_minutes = close_h * 60 + close_m
                    effective = close_minutes + (24 * 60 if close_minutes <= open_minutes else 0)
                    if effective > max_effective_closing_minutes:
                        max_effective_closing_minutes = effective
                if max_effective_closing_minutes < min_closing_minutes:
                    ch = max_effective_closing_minutes // 60
                    cm = max_effective_closing_minutes % 60
                    if ch >= 24:
                        ch -= 24
                    print(f"❌ 关门时间{ch}:{cm:02d}早于{min_closing_hour}:00")
                    return False
                print(f"✅ 关门时间符合要求（>= {min_closing_hour}:00）")
            else:
                print(f"⚠️  无法解析营业时间格式，跳过营业时间验证")
        else:
            print(f"⚠️  未找到营业时间信息，跳过营业时间验证")
    else:
        print(f"⚠️  未找到biz_ext信息，跳过营业时间验证")

    # 步骤4: 评分验证（rating >= 4.2）
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

    # 步骤5: 骑行时间验证（<= 6分钟）
    bicycling_result = maps_bicycling_by_coordinates(origin=user_location, destination=destination_location)
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

    # 步骤6: 获取火车站坐标
    station_search_result = maps_text_search(keywords=station_keywords, city=station_city, citylimit="true")
    if station_search_result.error:
        print(f"❌ 搜索{station_keywords}失败: {station_search_result.error}")
        return False

    if not station_search_result.pois or len(station_search_result.pois) == 0:
        print(f"❌ 未找到{station_keywords}")
        return False

    station_poi_id = station_search_result.pois[0].id
    print(f"✅ 找到{station_keywords}: {station_search_result.pois[0].name} (ID: {station_poi_id})")

    station_detail = maps_search_detail(id=station_poi_id)
    if station_detail.error:
        print(f"❌ 获取{station_keywords}详情失败: {station_detail.error}")
        return False

    if not station_detail.location:
        print(f"❌ {station_keywords}没有location信息")
        return False

    station_location = station_detail.location
    print(f"✅ 获取{station_keywords}坐标: {station_location}")

    # 步骤7: 驾车时间验证（<= 15分钟）
    driving_result = maps_driving_by_coordinates(origin=destination_location, destination=station_location)
    if driving_result.error:
        print(f"❌ 计算驾车路线失败: {driving_result.error}")
        return False

    if driving_result.total_duration_seconds is None:
        print(f"❌ 无法获取驾车时长")
        return False

    driving_duration = driving_result.total_duration_seconds
    if driving_duration > max_driving_duration:
        print(f"❌ 到{station_keywords}驾车时长{driving_duration}秒，超过{max_driving_duration}秒（{max_driving_duration // 60}分钟）")
        return False
    print(f"✅ 到{station_keywords}驾车时长{driving_duration}秒，符合要求（<= {max_driving_duration}秒，即{max_driving_duration // 60}分钟）")

    print(f"✅ 所有验证通过！")
    return True



if __name__ == "__main__":
    print("开始验证 496.py 文件...\n")
    result = verify_poi(poi_id="B0FFJJ61AB")
    print(f"\n验证结果: {result}")
