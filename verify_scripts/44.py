
"""
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 周边约束：调用 maps_around_search(location='126.975528,46.633971', radius='2000', keywords='酒吧')，验证返回pois中包含 poi_id='B0JRUX275M'。
2) 详情与营业时间：调用 maps_search_detail(id='B0JRUX275M')，获取 biz_ext.open_time / biz_ext.opentime2，验证其营业时间能覆盖到22:00。同时确保今天的一周中营业的时间。
3) 你步行时间上限：从 maps_search_detail 获取该POI的 location='126.982259,46.627080'；调用 maps_walking_by_coordinates(origin='126.975528,46.633971', destination='126.982259,46.627080')，验证 total_duration_seconds <= 900（15分钟）。
4) 获取 poi_id，再 maps_search_detail(id=poi_id) 获取 绥化站坐标：调用 maps_text_search(keywords='绥化站', city='绥化市') 取 poi_id，再 maps_search_detail(id=poi_id) 得到绥化站 location。
5) 你打车去火车站时间上限：调用 maps_driving_by_coordinates(origin='126.982259,46.627080', destination='127.015969,46.645209')，验证 total_duration_seconds <= 600（10分钟）。
6) 同事从绥化站打车来酒吧时间差：再调用 maps_driving_by_coordinates(origin='127.015969,46.645209', destination='126.982259,46.627080') 得到 t_colleague；用第5步得到的 t_you_to_station 作为对称参考（或直接以 t_you_from_station=第6步时长），验证 |t_colleague - t_you_from_station| <= 180（3分钟）。
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
    maps_walking_by_coordinates,
    maps_driving_by_coordinates
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str,
    user_location: str = "126.975528,46.633971",
    search_radius: int = 2000,  # 2km
    keywords: str = "酒吧",
    required_closing_time: str = "22:00",
    max_walking_duration: int = 900,  # 15 minutes = 900 seconds
    station_address: str = "绥化站",
    station_city: str = "绥化市",
    max_driving_duration: int = 600,  # 10 minutes = 600 seconds
    max_time_difference: int = 180,  # 3 minutes = 180 seconds
    current_time: str = "周六 20:00:00"  # 当前时间，格式为周* HH:MM:SS
) -> bool:
    """
    验证POI是否符合要求

    验证步骤：
    1) 周边约束：验证返回pois中包含 poi_id
    2) 详情与营业时间：验证营业时间能覆盖到22:00，且当前时间在营业时段内
    3) 步行时间上限：验证步行时长<=15分钟
    4) 获取 poi_id，再 maps_search_detail(id=poi_id) 获取 绥化站坐标
    5) 打车去火车站时间上限：验证驾车时长<=10分钟
    6) 同事从绥化站打车来酒吧时间差：验证时间差<=3分钟

    Args:
        poi_id: POI ID
        user_location: 用户坐标，格式为"经度,纬度"，默认"126.975528,46.633971"
        search_radius: 搜索半径（米），默认2000（2公里）
        keywords: 搜索关键词，默认"酒吧"
        required_closing_time: 要求的关闭时间，默认"22:00"
        max_walking_duration: 最大步行时长（秒），默认900（15分钟）
        station_address: 火车站地址，默认"绥化站"
        station_city: 火车站所在城市，默认"绥化市"
        max_driving_duration: 最大驾车时长（秒），默认600（10分钟）
        max_time_difference: 最大时间差（秒），默认180（3分钟）
        current_time: 当前时间，格式为周* HH:MM:SS，默认"周六 20:00:00"

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 周边约束（附近2公里内的酒吧）
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

    # 步骤2: 详情与营业时间
    poi_detail = maps_search_detail(id=poi_id)
    if poi_detail.error:
        print(f"❌ 获取POI详情失败: {poi_detail.error}")
        return False

    if not poi_detail.location:
        print(f"❌ POI没有location信息")
        return False

    poi_location = poi_detail.location
    print(f"✅ 获取POI坐标: {poi_location}")

    # 验证营业时间（能覆盖到22:00，且当前时间在营业时段内）
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
                    # 验证营业时间能覆盖到22:00（关闭时间 >= 22:00）
                    required_time_match = re.match(r'(\d{1,2}):(\d{2})', required_closing_time)
                    if required_time_match:
                        required_hour = int(required_time_match.group(1))
                        required_minute = int(required_time_match.group(2))
                        required_time_minutes = required_hour * 60 + required_minute

                        # 检查是否有任一时段的关闭时间 >= 22:00（含跨天：关门在次日则有效关门按+24*60）
                        covers_required_time = False
                        for match in matches:
                            open_hour = int(match[0])
                            open_minute = int(match[1])
                            close_hour = int(match[2])
                            close_minute = int(match[3])
                            open_time_minutes = open_hour * 60 + open_minute
                            close_time_minutes = close_hour * 60 + close_minute
                            if close_time_minutes <= open_time_minutes:
                                close_time_minutes += 24 * 60  # 跨天，有效关门在次日
                            if close_time_minutes >= required_time_minutes:
                                covers_required_time = True
                                break

                        if not covers_required_time:
                            print(f"❌ 营业时间未覆盖到{required_closing_time}")
                            return False
                        print(f"✅ 营业时间覆盖到{required_closing_time}，符合要求")

                    # 检查当前时间是否在任一营业时段内（含跨天：关门在次日则 在段内 = current>=open 或 current<=close）
                    is_open = False
                    for match in matches:
                        open_hour = int(match[0])
                        open_minute = int(match[1])
                        close_hour = int(match[2])
                        close_minute = int(match[3])

                        open_time_minutes = open_hour * 60 + open_minute
                        close_time_minutes = close_hour * 60 + close_minute

                        # 判断当前时间是否在营业时段内
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
                    print(f"⚠️  无法解析营业时间格式，跳过营业时间验证")
            else:
                print(f"⚠️  无法解析当前时间格式，跳过营业时间验证")
        else:
            print(f"⚠️  未找到营业时间信息，跳过营业时间验证")
    else:
        print(f"⚠️  未找到biz_ext信息，跳过营业时间验证")

    # 步骤3: 步行时间上限（<= 15分钟）
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

    # 步骤4: 获取绥化站坐标（用 maps_text_search + maps_search_detail 替代 maps_geo）
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

    # 步骤5: 打车去火车站时间上限（<= 10分钟）
    driving_to_station_result = maps_driving_by_coordinates(origin=poi_location, destination=station_location)
    if driving_to_station_result.error:
        print(f"❌ 计算到{station_address}驾车路线失败: {driving_to_station_result.error}")
        return False

    if driving_to_station_result.total_duration_seconds is None:
        print(f"❌ 无法获取到{station_address}驾车时长")
        return False

    t_you_to_station = driving_to_station_result.total_duration_seconds
    if t_you_to_station > max_driving_duration:
        print(f"❌ 到{station_address}驾车时长{t_you_to_station}秒，超过{max_driving_duration}秒（{max_driving_duration // 60}分钟）")
        return False
    print(f"✅ 到{station_address}驾车时长{t_you_to_station}秒，符合要求（<= {max_driving_duration}秒，即{max_driving_duration // 60}分钟）")

    # 步骤6: 同事从绥化站打车来酒吧时间差（<= 3分钟）
    driving_from_station_result = maps_driving_by_coordinates(origin=station_location, destination=poi_location)
    if driving_from_station_result.error:
        print(f"❌ 计算从{station_address}驾车路线失败: {driving_from_station_result.error}")
        return False

    if driving_from_station_result.total_duration_seconds is None:
        print(f"❌ 无法获取从{station_address}驾车时长")
        return False

    t_colleague = driving_from_station_result.total_duration_seconds
    print(f"✅ 从{station_address}驾车时长{t_colleague}秒")

    # 验证时间差（|t_colleague - t_you_to_station| <= 3分钟）
    time_diff = abs(t_colleague - t_you_to_station)
    if time_diff > max_time_difference:
        print(f"❌ 驾车时间差{time_diff}秒，超过{max_time_difference}秒（{max_time_difference // 60}分钟）")
        return False
    print(f"✅ 驾车时间差{time_diff}秒，符合要求（<= {max_time_difference}秒，即{max_time_difference // 60}分钟）")

    print(f"✅ 所有验证通过！")
    return True



if __name__ == "__main__":
    print("开始验证 582.py 文件...\n")
    result = verify_poi(poi_id="B0JRUX275M")
    print(f"\n验证结果: {result}")

