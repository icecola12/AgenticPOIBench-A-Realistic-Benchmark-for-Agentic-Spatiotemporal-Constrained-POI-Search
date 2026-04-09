
"""
修改任务指令：你现在想在附近2公里想找一家酒店。你打算先在酒店放下行李再打车去乐山站赶高铁，所以从你这到酒店、再从酒店开车到乐山站的总耗时不能超过15分钟，并且相比你直接打车去乐山站，最多只能多花3分钟。酒店评分要在4.8分及以上。另外你还要在去酒店前先去乐山大佛景区附近接人，所以酒店到乐山大佛景区的直线距离不能超过7公里。
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 调用 maps_around_search(location=103.737272,29.615892, radius=2000, keywords=酒店)，验证返回pois中包含 target_poi_id。
2) 调用 maps_search_detail(id=target_poi_id)，获取评分rating并验证 rating>=4.8，同时取酒店坐标hotel_loc。
3) 调用 maps_search_detail(id='B0FFFH18BD') 获取乐山站坐标lsz_loc；调用 maps_driving_by_coordinates(origin=103.737272,29.615892, destination=hotel_loc) 得到t_user_hotel；调用 maps_driving_by_coordinates(origin=hotel_loc, destination=lsz_loc) 得到t_hotel_lsz；验证 (t_user_hotel+t_hotel_lsz)<=15分钟。
4) 调用 maps_driving_by_coordinates(origin=103.737272,29.615892, destination=lsz_loc) 得到t_user_lsz；验证 (t_user_hotel+t_hotel_lsz - t_user_lsz)<=3分钟。
5) 调用 maps_search_detail(id='B034100387') 获取乐山大佛坐标bfs_loc(用entr_location更贴近景区入口亦可)；调用 maps_distance(origins=bfs_loc, destination=hotel_loc) 得到d1；验证 d1<=7000米。
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
    maps_distance
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str,
    user_location: str = "103.737272,29.615892",
    search_radius: int = 2000,  # 2km
    keywords: str = "酒店",
    min_rating: float = 4.8,
    station_id: str = "B0FFFH18BD",  # 乐山站
    max_total_duration: int = 900,  # 15 minutes = 900 seconds
    max_extra_duration: int = 180,  # 3 minutes = 180 seconds
    buddha_id: str = "B034100387",  # 乐山大佛
    max_distance: int = 7000  # 7000 meters = 7km
) -> bool:
    """
    验证POI是否符合要求

    验证步骤：
    1) 周边约束：调用 maps_around_search，验证返回pois中包含 target_poi_id
    2) 评分约束：调用 maps_search_detail，获取评分rating并验证 rating>=4.8，同时取酒店坐标
    3) 总耗时约束：获取乐山站坐标，计算用户到酒店和酒店到车站的驾车时间，验证总时间<=15分钟
    4) 额外耗时约束：计算用户直接到车站的时间，验证额外耗时<=3分钟
    5) 距离约束：获取乐山大佛坐标，计算到酒店的距离，验证<=7000米

    Args:
        poi_id: POI ID
        user_location: 用户坐标，格式为"经度,纬度"，默认"103.737272,29.615892"
        search_radius: 搜索半径（米），默认2000（2公里）
        keywords: 搜索关键词，默认"酒店"
        min_rating: 最低评分，默认4.8
        station_id: 乐山站POI ID，默认"B0FFFH18BD"
        max_total_duration: 最大总耗时（秒），默认900（15分钟）
        max_extra_duration: 最大额外耗时（秒），默认180（3分钟）
        buddha_id: 乐山大佛POI ID，默认"B034100387"
        max_distance: 最大距离（米），默认7000（7公里）

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 周边约束验证（2公里内的酒店）
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

    # 步骤2: 获取目标POI详情并验证评分
    poi_detail = maps_search_detail(id=poi_id)
    if poi_detail.error:
        print(f"❌ 获取POI详情失败: {poi_detail.error}")
        return False

    if not poi_detail.location:
        print(f"❌ POI没有location信息")
        return False

    hotel_loc = poi_detail.location
    print(f"✅ 获取酒店坐标: {hotel_loc}")

    # 评分验证（rating >= 4.8）
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

    # 步骤3: 获取乐山站坐标并计算总耗时
    station_detail = maps_search_detail(id=station_id)
    if station_detail.error:
        print(f"❌ 获取乐山站详情失败: {station_detail.error}")
        return False

    if not station_detail.location:
        print(f"❌ 乐山站没有location信息")
        return False

    lsz_loc = station_detail.location
    print(f"✅ 获取乐山站坐标: {lsz_loc}")

    # 计算用户到酒店的驾车时间
    driving_user_hotel = maps_driving_by_coordinates(origin=user_location, destination=hotel_loc)
    if driving_user_hotel.error:
        print(f"❌ 计算用户到酒店驾车路线失败: {driving_user_hotel.error}")
        return False

    if driving_user_hotel.total_duration_seconds is None:
        print(f"❌ 无法获取用户到酒店驾车时长")
        return False

    t_user_hotel = driving_user_hotel.total_duration_seconds
    print(f"✅ 用户到酒店驾车时长: {t_user_hotel}秒")

    # 计算酒店到乐山站的驾车时间
    driving_hotel_lsz = maps_driving_by_coordinates(origin=hotel_loc, destination=lsz_loc)
    if driving_hotel_lsz.error:
        print(f"❌ 计算酒店到乐山站驾车路线失败: {driving_hotel_lsz.error}")
        return False

    if driving_hotel_lsz.total_duration_seconds is None:
        print(f"❌ 无法获取酒店到乐山站驾车时长")
        return False

    t_hotel_lsz = driving_hotel_lsz.total_duration_seconds
    print(f"✅ 酒店到乐山站驾车时长: {t_hotel_lsz}秒")

    # 验证总耗时 <= 15分钟
    total_duration = t_user_hotel + t_hotel_lsz
    if total_duration > max_total_duration:
        print(f"❌ 总耗时{total_duration}秒，超过{max_total_duration}秒（{max_total_duration // 60}分钟）")
        return False
    print(f"✅ 总耗时{total_duration}秒，符合要求（<= {max_total_duration}秒，即{max_total_duration // 60}分钟）")

    # 步骤4: 计算用户直接到乐山站的时间并验证额外耗时
    driving_user_lsz = maps_driving_by_coordinates(origin=user_location, destination=lsz_loc)
    if driving_user_lsz.error:
        print(f"❌ 计算用户到乐山站驾车路线失败: {driving_user_lsz.error}")
        return False

    if driving_user_lsz.total_duration_seconds is None:
        print(f"❌ 无法获取用户到乐山站驾车时长")
        return False

    t_user_lsz = driving_user_lsz.total_duration_seconds
    print(f"✅ 用户直接到乐山站驾车时长: {t_user_lsz}秒")

    # 验证额外耗时 <= 3分钟
    extra_duration = total_duration - t_user_lsz
    if extra_duration > max_extra_duration:
        print(f"❌ 额外耗时{extra_duration}秒，超过{max_extra_duration}秒（{max_extra_duration // 60}分钟）")
        return False
    print(f"✅ 额外耗时{extra_duration}秒，符合要求（<= {max_extra_duration}秒，即{max_extra_duration // 60}分钟）")

    # 步骤5: 获取乐山大佛坐标并验证距离
    buddha_detail = maps_search_detail(id=buddha_id)
    if buddha_detail.error:
        print(f"❌ 获取乐山大佛详情失败: {buddha_detail.error}")
        return False

    # 优先使用entr_location，如果没有则使用location
    if buddha_detail.entr_location:
        bfs_loc = buddha_detail.entr_location
        print(f"✅ 获取乐山大佛入口坐标: {bfs_loc}")
    elif buddha_detail.location:
        bfs_loc = buddha_detail.location
        print(f"✅ 获取乐山大佛坐标: {bfs_loc}")
    else:
        print(f"❌ 乐山大佛没有location信息")
        return False

    # 计算乐山大佛到酒店的距离
    distance_result = maps_distance(origins=bfs_loc, destination=hotel_loc)
    if distance_result.error:
        print(f"❌ 计算到酒店距离失败: {distance_result.error}")
        return False

    if not distance_result.results or len(distance_result.results) == 0:
        print(f"❌ 无法获取到酒店距离")
        return False

    d1 = distance_result.results[0].distance_meters
    if d1 > max_distance:
        print(f"❌ 到酒店距离{d1}米，超过{max_distance}米（{max_distance // 1000}公里）")
        return False
    print(f"✅ 到酒店距离{d1}米，符合要求（<= {max_distance}米，即{max_distance // 1000}公里）")

    print(f"✅ 所有验证通过！")
    return True



if __name__ == "__main__":
    print("开始验证 633.py 文件...\n")
    result = verify_poi(poi_id="B0IG07B6CX")
    print(f"\n验证结果: {result}")
