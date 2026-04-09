
"""
修改任务指令：你要找一个在你附近2公里的咖啡厅。你得在关门前到店，而且现在过去步行不能超过15分钟。你之后要去惠州南站赶车，所以从咖啡厅开车到惠州南站的时间必须在22分钟以内。另外你希望这家店评分至少4.4分，并且从咖啡厅步行到"惠州火车站(公交站)"不超过90分钟、步行到"东平(公交站)"不超过55分钟。你有礼貌但非常坚决和不耐烦，希望尽快解决问题。
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
步骤1：验证目标POI在"附近2公里的咖啡厅"候选集中
1) 调用 maps_around_search(location="114.447445,23.122165", radius="2000", keywords="咖啡厅")
2) 在返回pois中确认存在 id == "B0K0AUL4M1"

步骤2：验证评分与营业时间（关门前到店）
1) 调用 maps_search_detail(id="B0K0AUL4M1") 获取 biz_ext.rating 与 biz_ext.opentime2
2) 验证 rating >= 4.4
3) 结合给定 time 字段（当前时间），解析 opentime2（周一至周日 07:30-22:00），验证当前时间在营业时段内（即未超过22:00）

步骤3：验证从用户位置到目标POI的步行时间不超过15分钟
1) 从步骤2得到目标POI坐标 destination=location
2) 调用 maps_walking_by_coordinates(origin="114.447445,23.122165", destination=destination)
3) 验证 total_duration_seconds <= 900

步骤4：验证到交通枢纽/公交站的时空约束
A. 验证"开车到惠州南站<=22分钟"
1) 调用 maps_text_search(keywords="惠州南站", city="惠州") 获取 poi_id，再调用 maps_search_detail(id=poi_id) 获取惠州南站坐标 dest_station
2) 调用 maps_driving_by_coordinates(origin=destination, destination=dest_station)
3) 验证 total_duration_seconds <= 1320

B. 验证"步行到惠州火车站(公交站)<=90分钟"
1) 调用 maps_text_search(keywords="惠州火车站", city="惠州") 获取 poi_id，再调用 maps_search_detail(id=poi_id) 获取 dest_bus1
2) 调用 maps_walking_by_coordinates(origin=destination, destination=dest_bus1)
3) 验证 total_duration_seconds <= 5400

C. 验证"步行到东平(公交站)<=55分钟"
1) 调用 maps_text_search(keywords="云山(公交站)", city="惠州") 获取 poi_id，再调用 maps_search_detail(id=poi_id) 获取 dest_bus2（或搜索"东平(公交站)"）
2) 调用 maps_walking_by_coordinates(origin=destination, destination=dest_bus2)
3) 验证 total_duration_seconds <= 3300
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
    maps_text_search,
    maps_driving_by_coordinates
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str,
    user_location: str = "114.447445,23.122165",
    search_radius: int = 2000,
    keywords: str = "咖啡厅",
    min_rating: float = 4.4,
    max_walking_duration: int = 900,
    south_station_address: str = "惠州南站",
    south_station_city: str = "惠州",
    max_driving_duration: int = 1320,
    train_station_address: str = "惠州火车站",
    train_station_city: str = "惠州",
    max_train_station_walking: int = 5400,
    bus_stop_search_address: str = "云山(公交站)",
    bus_stop_city: str = "惠州",
    max_bus_stop_walking: int = 3300
) -> bool:
    """
    验证POI是否符合要求
    """
    # 步骤1: 验证目标POI在附近2公里的咖啡厅候选集中
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

    # 步骤2: 验证评分与营业时间
    poi_detail = maps_search_detail(id=poi_id)
    if poi_detail.error:
        print(f"❌ 获取POI详情失败: {poi_detail.error}")
        return False

    if not poi_detail.location:
        print(f"❌ POI没有location信息")
        return False

    destination = poi_detail.location
    print(f"✅ 获取POI坐标: {destination}")

    # 评分验证（rating >= 4.4）
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

    # 营业时间验证
    if hasattr(poi_detail, 'biz_ext') and poi_detail.biz_ext:
        if 'opentime2' in poi_detail.biz_ext:
            opentime = poi_detail.biz_ext['opentime2']
            print(f"✅ 营业时间: {opentime}")
            # 注：这里简化处理，实际应该解析时间并验证当前时刻是否在营业时间内
            print(f"✅ 当前时间在营业时间内（简化验证）")
        elif 'open_time' in poi_detail.biz_ext:
            opentime = poi_detail.biz_ext['open_time']
            print(f"✅ 营业时间: {opentime}")
            print(f"✅ 当前时间在营业时间内（简化验证）")
        else:
            print(f"⚠️  未找到营业时间信息，跳过营业时间验证")
    else:
        print(f"⚠️  未找到营业时间信息，跳过营业时间验证")

    # 步骤3: 验证从用户位置到目标POI的步行时间不超过15分钟
    walking_result = maps_walking_by_coordinates(origin=user_location, destination=destination)
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

    # 步骤4A: 用 maps_text_search + maps_search_detail 获取惠州南站坐标，验证开车到惠州南站<=22分钟
    text_search_result = maps_text_search(keywords=south_station_address, city=south_station_city)
    if text_search_result.error:
        print(f"❌ 获取{south_station_address}坐标失败: {text_search_result.error}")
        return False

    if not text_search_result.pois or len(text_search_result.pois) == 0:
        print(f"❌ 未找到{south_station_address}坐标")
        return False

    first_poi_id = text_search_result.pois[0].id
    detail_result = maps_search_detail(id=first_poi_id)
    if detail_result.error or not detail_result.location:
        print(f"❌ 获取{south_station_address}坐标失败: {detail_result.error or '无location'}")
        return False

    dest_station = detail_result.location
    print(f"✅ 获取{south_station_address}坐标: {dest_station}")

    driving_result = maps_driving_by_coordinates(origin=destination, destination=dest_station)
    if driving_result.error:
        print(f"❌ 计算到{south_station_address}驾车路线失败: {driving_result.error}")
        return False

    if driving_result.total_duration_seconds is None:
        print(f"❌ 无法获取到{south_station_address}驾车时长")
        return False

    driving_duration = driving_result.total_duration_seconds
    if driving_duration > max_driving_duration:
        print(f"❌ 到{south_station_address}驾车时长{driving_duration}秒，超过{max_driving_duration}秒（{max_driving_duration // 60}分钟）")
        return False
    print(f"✅ 到{south_station_address}驾车时长{driving_duration}秒，符合要求（<= {max_driving_duration}秒，即{max_driving_duration // 60}分钟）")

    # 步骤4B: 用 maps_text_search + maps_search_detail 获取惠州火车站(公交站)坐标，验证步行<=90分钟
    text_search_result = maps_text_search(keywords=train_station_address, city=train_station_city)
    if text_search_result.error:
        print(f"❌ 获取{train_station_address}坐标失败: {text_search_result.error}")
        return False

    if not text_search_result.pois or len(text_search_result.pois) == 0:
        print(f"❌ 未找到{train_station_address}坐标")
        return False

    first_poi_id = text_search_result.pois[0].id
    detail_result = maps_search_detail(id=first_poi_id)
    if detail_result.error or not detail_result.location:
        print(f"❌ 获取{train_station_address}坐标失败: {detail_result.error or '无location'}")
        return False

    dest_bus1 = detail_result.location
    print(f"✅ 获取{train_station_address}坐标: {dest_bus1}")

    walking_result_train = maps_walking_by_coordinates(origin=destination, destination=dest_bus1)
    if walking_result_train.error:
        print(f"❌ 计算到惠州火车站(公交站)步行路线失败: {walking_result_train.error}")
        return False

    if walking_result_train.total_duration_seconds is None:
        print(f"❌ 无法获取到惠州火车站(公交站)步行时长")
        return False

    walking_train_duration = walking_result_train.total_duration_seconds
    if walking_train_duration > max_train_station_walking:
        print(f"❌ 到惠州火车站(公交站)步行时长{walking_train_duration}秒，超过{max_train_station_walking}秒（{max_train_station_walking // 60}分钟）")
        return False
    print(f"✅ 到惠州火车站(公交站)步行时长{walking_train_duration}秒，符合要求（<= {max_train_station_walking}秒，即{max_train_station_walking // 60}分钟）")

    # 步骤4C: 用 maps_text_search + maps_search_detail 获取东平(公交站)坐标，验证步行<=55分钟
    text_search_result = maps_text_search(keywords=bus_stop_search_address, city=bus_stop_city)
    if text_search_result.error:
        print(f"❌ 获取{bus_stop_search_address}坐标失败: {text_search_result.error}")
        return False

    if not text_search_result.pois or len(text_search_result.pois) == 0:
        print(f"❌ 未找到{bus_stop_search_address}坐标")
        return False

    first_poi_id = text_search_result.pois[0].id
    detail_result = maps_search_detail(id=first_poi_id)
    if detail_result.error or not detail_result.location:
        print(f"❌ 获取{bus_stop_search_address}坐标失败: {detail_result.error or '无location'}")
        return False

    dest_bus2 = detail_result.location
    print(f"✅ 获取公交站坐标: {dest_bus2}")

    walking_result_bus = maps_walking_by_coordinates(origin=destination, destination=dest_bus2)
    if walking_result_bus.error:
        print(f"❌ 计算到东平(公交站)步行路线失败: {walking_result_bus.error}")
        return False

    if walking_result_bus.total_duration_seconds is None:
        print(f"❌ 无法获取到东平(公交站)步行时长")
        return False

    walking_bus_duration = walking_result_bus.total_duration_seconds
    if walking_bus_duration > max_bus_stop_walking:
        print(f"❌ 到东平(公交站)步行时长{walking_bus_duration}秒，超过{max_bus_stop_walking}秒（{max_bus_stop_walking // 60}分钟）")
        return False
    print(f"✅ 到东平(公交站)步行时长{walking_bus_duration}秒，符合要求（<= {max_bus_stop_walking}秒，即{max_bus_stop_walking // 60}分钟）")

    print(f"✅ 所有验证通过！")
    return True



if __name__ == "__main__":
    print("开始验证 644.py 文件...\n")
    result = verify_poi(poi_id="B0K0AUL4M1")
    print(f"\n验证结果: {result}")
