
"""
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 验证候选POI来自'附近2km内'的周边搜索结果
- 调用 maps_around_search(location="114.435617,23.12905", radius="2000", keywords="咖啡")。
- 在返回的 pois 列表中查找是否存在 id=="B0KRKS1926"；若存在则满足"附近2km内"。

2) 验证评分与营业状态
- 调用 maps_search_detail(id="B0KRKS1926") 获取 biz_ext.rating 与 biz_ext.open_time/opentime2。
- 验证 rating >= 4.3。
- 结合本条目给定 time 字段（当前时间），判断当前时间是否落在 open_time/opentime2 描述的营业时段内；若落在营业时段内则满足"现在还在营业"。

3) 验证骑行时间不超过7分钟
- 从步骤2的 maps_search_detail 读取目标POI的 location 作为 destination。
- 调用 maps_bicycling_by_coordinates(origin="114.435617,23.12905", destination=destination)。
- 验证 total_duration_seconds <= 7*60。

4) 验证公交站距离与'经由该店去佳兆业广场'的时间拓扑约束
4.1 公交站距离：
- 调用 maps_around_search(location=destination, radius="500", keywords="公交站")。
- 验证返回 pois 数量 >= 1（表示500米内存在公交站）。

4.2 时间拓扑（经由POI到佳兆业广场不绕太多）：
- 调用 maps_text_search(keywords="佳兆业广场(惠州)", city="惠州") 得到 poi_id，再 maps_search_detail(id=poi_id) 获取 location 作为 jzyloc。
- 调用 maps_walking_by_coordinates(origin="114.435617,23.12905", destination=jzyloc)，得到 direct_walk_sec。
- 调用 maps_bicycling_by_coordinates(origin="114.435617,23.12905", destination=destination)，得到 bike_to_poi_sec。
- 调用 maps_walking_by_coordinates(origin=destination, destination=jzyloc)，得到 walk_poi_to_jzy_sec。
- 计算 via_poi_sec = bike_to_poi_sec + walk_poi_to_jzy_sec。
- 验证 via_poi_sec - direct_walk_sec <= 5*60。
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
    maps_bicycling_by_coordinates,
    maps_walking_by_coordinates
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str,
    user_location: str = "114.435617,23.12905",
    search_radius: int = 2000,  # 2km
    keywords: str = "咖啡",
    min_rating: float = 4.3,
    max_bicycling_duration: int = 420,  # 7 minutes = 420 seconds
    bus_stop_search_radius: int = 500,  # 500 meters
    bus_stop_keywords: str = "公交站",
    min_bus_stop_count: int = 1,
    destination_address: str = "佳兆业广场(惠州)",
    destination_city: str = "惠州",
    max_time_difference: int = 300,  # 5 minutes = 300 seconds
    current_time: str = "周二 19:40:00"  # 当前时间，格式为周* HH:MM:SS
) -> bool:
    """
    验证POI是否符合要求

    验证步骤：
    1) 验证候选POI来自'附近2km内'的周边搜索结果
    2) 验证评分与营业状态
    3) 验证骑行时间不超过7分钟
    4) 验证公交站距离与'经由该店去佳兆业广场'的时间拓扑约束

    Args:
        poi_id: POI ID
        user_location: 用户坐标，格式为"经度,纬度"，默认"114.435617,23.12905"
        search_radius: 搜索半径（米），默认2000（2公里）
        keywords: 搜索关键词，默认"咖啡"
        min_rating: 最低评分，默认4.3
        max_bicycling_duration: 最大骑行时长（秒），默认420（7分钟）
        bus_stop_search_radius: 公交站搜索半径（米），默认500
        bus_stop_keywords: 公交站搜索关键词，默认"公交站"
        min_bus_stop_count: 最少公交站数量，默认1
        destination_address: 目的地地址，默认"佳兆业广场(惠州)"
        destination_city: 目的地所在城市，默认"惠州"
        max_time_difference: 经由POI与直达的最大时间差（秒），默认300（5分钟）
        current_time: 当前时间，格式为周* HH:MM:SS，默认"周二 19:40:00"

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 验证候选POI来自'附近2km内'的周边搜索结果
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

    # 步骤2: 验证评分与营业状态
    poi_detail = maps_search_detail(id=poi_id)
    if poi_detail.error:
        print(f"❌ 获取POI详情失败: {poi_detail.error}")
        return False

    if not poi_detail.location:
        print(f"❌ POI没有location信息")
        return False

    poi_location = poi_detail.location
    print(f"✅ 获取POI坐标: {poi_location}")

    # 验证评分（rating >= 4.3）
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

    # 验证营业状态（判断当前时间是否在营业时段内）
    if hasattr(poi_detail, 'biz_ext') and poi_detail.biz_ext:
        opentime = None
        # biz_ext 是字典类型，需要使用字典键访问方式
        if 'opentime2' in poi_detail.biz_ext and poi_detail.biz_ext['opentime2']:
            opentime = poi_detail.biz_ext['opentime2']
        elif 'open_time' in poi_detail.biz_ext and poi_detail.biz_ext['open_time']:
            opentime = poi_detail.biz_ext['open_time']

        if opentime:
            print(f"✅ 营业时间: {opentime}")
            print(f"✅ 当前时间: {current_time}")

            # 解析当前时间（格式：周* HH:MM:SS）
            import re
            current_time_match = re.search(r'(\d{1,2}):(\d{2}):(\d{2})', current_time)
            if current_time_match:
                current_hour = int(current_time_match.group(1))
                current_minute = int(current_time_match.group(2))
                current_time_minutes = current_hour * 60 + current_minute

                # 解析营业时间（假设格式为 "HH:MM-HH:MM" 或 "周一至周日 HH:MM-HH:MM"）
                time_pattern = r'(\d{1,2}):(\d{2})-(\d{1,2}):(\d{2})'
                matches = re.findall(time_pattern, opentime)

                if matches:
                    # 检查当前时间是否在任一营业时段内
                    is_open = False
                    for match in matches:
                        open_hour = int(match[0])
                        open_minute = int(match[1])
                        close_hour = int(match[2])
                        close_minute = int(match[3])

                        open_time_minutes = open_hour * 60 + open_minute
                        close_time_minutes = close_hour * 60 + close_minute

                        # 判断当前时间是否在营业时段内（含跨天：关门在次日则 在段内 = current>=open 或 current<=close）
                        if close_time_minutes < open_time_minutes:
                            # 跨天时段：当前在开门之后或关门之前
                            if current_time_minutes >= open_time_minutes or current_time_minutes <= close_time_minutes:
                                is_open = True
                                break
                        else:
                            if open_time_minutes <= current_time_minutes <= close_time_minutes:
                                is_open = True
                                break

                    if not is_open:
                        print(f"❌ 当前时间{current_time}不在营业时段内")
                        return False
                    print(f"✅ 当前时间在营业时段内，符合要求")
                else:
                    print(f"⚠️  无法解析营业时间格式，跳过营业状态验证")
            else:
                print(f"⚠️  无法解析当前时间格式，跳过营业状态验证")
        else:
            print(f"⚠️  未找到营业时间信息，跳过营业状态验证")
    else:
        print(f"⚠️  未找到biz_ext信息，跳过营业状态验证")

    # 步骤3: 验证骑行时间不超过7分钟
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

    # 步骤4.1: 验证公交站距离（500米内存在公交站）
    bus_stop_search_result = maps_around_search(
        location=poi_location,
        radius=str(bus_stop_search_radius),
        keywords=bus_stop_keywords
    )
    if bus_stop_search_result.error:
        print(f"❌ 搜索公交站失败: {bus_stop_search_result.error}")
        return False

    if not bus_stop_search_result.pois or len(bus_stop_search_result.pois) < min_bus_stop_count:
        print(f"❌ {bus_stop_search_radius}米内公交站数量不足{min_bus_stop_count}个")
        return False

    bus_stop_count = len(bus_stop_search_result.pois)
    print(f"✅ {bus_stop_search_radius}米内找到{bus_stop_count}个公交站，符合要求（>= {min_bus_stop_count}个）")

    # 步骤4.2: 验证时间拓扑（经由POI到佳兆业广场不绕太多）
    # 获取佳兆业广场坐标（用 maps_text_search + maps_search_detail 替代 maps_geo）
    text_search_result = maps_text_search(keywords=destination_address, city=destination_city)
    if text_search_result.error:
        print(f"❌ 获取{destination_address}坐标失败: {text_search_result.error}")
        return False

    if not text_search_result.pois or len(text_search_result.pois) == 0:
        print(f"❌ 未找到{destination_address}坐标")
        return False

    first_poi_id = text_search_result.pois[0].id
    detail_result = maps_search_detail(id=first_poi_id)

    if detail_result.error:

        print(f"❌ 获取坐标失败: {detail_result.error}")

        return False

    if not detail_result.location:

        print("❌ 未获取到坐标")

        return False

    jzy_location = detail_result.location
    print(f"✅ 获取{destination_address}坐标: {jzy_location}")

    # 计算直达步行时间
    direct_walk_result = maps_walking_by_coordinates(origin=user_location, destination=jzy_location)
    if direct_walk_result.error:
        print(f"❌ 计算直达步行路线失败: {direct_walk_result.error}")
        return False

    if direct_walk_result.total_duration_seconds is None:
        print(f"❌ 无法获取直达步行时长")
        return False

    direct_walk_sec = direct_walk_result.total_duration_seconds
    print(f"✅ 直达步行时长{direct_walk_sec}秒")

    # 计算经由POI的时间（骑行到POI + 从POI步行到佳兆业广场）
    bike_to_poi_sec = bicycling_duration  # 已在步骤3计算

    walk_poi_to_jzy_result = maps_walking_by_coordinates(origin=poi_location, destination=jzy_location)
    if walk_poi_to_jzy_result.error:
        print(f"❌ 计算从POI到{destination_address}步行路线失败: {walk_poi_to_jzy_result.error}")
        return False

    if walk_poi_to_jzy_result.total_duration_seconds is None:
        print(f"❌ 无法获取从POI到{destination_address}步行时长")
        return False

    walk_poi_to_jzy_sec = walk_poi_to_jzy_result.total_duration_seconds
    print(f"✅ 从POI到{destination_address}步行时长{walk_poi_to_jzy_sec}秒")

    via_poi_sec = bike_to_poi_sec + walk_poi_to_jzy_sec
    time_diff = via_poi_sec - direct_walk_sec

    if time_diff > max_time_difference:
        print(f"❌ 经由POI时间{via_poi_sec}秒与直达时间{direct_walk_sec}秒的差值{time_diff}秒，超过{max_time_difference}秒（{max_time_difference // 60}分钟）")
        return False
    print(f"✅ 经由POI时间{via_poi_sec}秒与直达时间{direct_walk_sec}秒的差值{time_diff}秒，符合要求（<= {max_time_difference}秒，即{max_time_difference // 60}分钟）")

    print(f"✅ 所有验证通过！")
    return True



if __name__ == "__main__":
    print("开始验证 497.py 文件...\n")
    result = verify_poi(poi_id="B0KRKS1926")
    print(f"\n验证结果: {result}")
