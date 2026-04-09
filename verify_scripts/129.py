"""
修改任务指令：你要在附近2000米以内找一家电竞馆。你希望你走路到那里的距离不要超过1300米。到了之后你打算坐地铁走，所以这个电竞馆走到附近1500米范围内最近的地铁站，步行不要超过15分钟。另外你要和朋友在那儿会合：朋友从合肥火车站开车过去，他开车到电竞馆的时间需要比你走路到电竞馆的时间至少少8分钟。最后，为了你们到店后取现金方便，电竞馆300米内必须能找到ATM。你有礼貌但非常坚决和不耐烦，希望尽快解决问题。
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 附近2000米：调用 maps_around_search(location='117.285236,31.872469', radius='2000', keywords='电竞馆')，验证返回pois中包含 target_poi_id='B0LDD7HSX7'。  
2) 你步行距离≤1300米：先 maps_search_detail('B0LDD7HSX7') 得到目标坐标destination；再调用 maps_walking_by_coordinates(origin='117.285236,31.872469', destination=destination)，验证 total_distance_meters ≤ 1300。  
3) 最近地铁站步行≤15分钟（且地铁站在电竞馆1500米范围内）：  
   a. 调用 maps_search_detail('B0LDD7HSX7') 获取电竞馆坐标L。  
   b. 调用 maps_around_search(location=L, radius='1500', keywords='地铁站') 获取候选地铁站列表S。  
   c. 对S中每个地铁站i，调用 maps_walking_by_coordinates(origin=L, destination=i.location) 得到步行时间ti；取最小值t_min，验证 t_min ≤ 900秒。  
4) 朋友（合肥火车站）开车比你步行至少快8分钟：  
   a. maps_geo(address='合肥火车站', city='合肥') 得到朋友起点坐标O。  
   b. maps_search_detail('B0LDD7HSX7') 得到电竞馆坐标D。  
   c. 调用 maps_driving_by_coordinates(origin=O, destination=D) 得到驾车时间 t_drive。  
   d. 调用 maps_walking_by_coordinates(origin='117.285236,31.872469', destination=D) 得到你的步行时间 t_walk。  
   e. 验证 (t_walk - t_drive) ≥ 480秒。  
5) 电竞馆300米内有ATM：调用 maps_around_search(location=D, radius='300', keywords='ATM')，验证返回pois数量>0。
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
    maps_walking_by_coordinates,
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str,
    user_location: str = "117.285236,31.872469",
    search_radius: int = 2000,
    keywords: str = "电竞馆",
    max_walking_distance: int = 1300,  # 1300米
    subway_search_radius: int = 1500,
    subway_keywords: str = "地铁站",
    max_subway_walking_seconds: int = 900,  # 15分钟 = 900秒
    friend_start_address: str = "合肥火车站",
    friend_start_city: str = "合肥",
    min_drive_faster_seconds: int = 480,  # 至少快8分钟 = 480秒
    atm_search_radius: int = 300,
    atm_keywords: str = "ATM",
) -> bool:
    """
    验证POI是否符合要求

    验证步骤：
    1) 附近2000米：调用 maps_around_search，验证返回pois中包含目标poi_id。
    2) 你步行距离≤1300米：maps_search_detail 得到目标坐标，maps_walking_by_coordinates 验证 total_distance_meters ≤ 1300。
    3) 最近地铁站步行≤15分钟（且地铁站在电竞馆1500米范围内）：获取电竞馆坐标L，maps_around_search 获取地铁站列表，对每个站点计算步行时间取最小值，验证 ≤ 900秒。
    4) 朋友（合肥火车站）开车比你步行至少快8分钟：获取朋友起点O、电竞馆D，计算 t_drive 和 t_walk，验证 (t_walk - t_drive) ≥ 480秒。
    5) 电竞馆300米内有ATM：maps_around_search(location=D, radius='300', keywords='ATM')，验证 pois 数量 > 0。

    Args:
        poi_id: POI ID，默认"B0LDD7HSX7"
        user_location: 用户坐标，格式为"经度,纬度"，默认"117.285236,31.872469"
        search_radius: 搜索半径（米），默认2000
        keywords: 搜索关键词，默认"电竞馆"
        max_walking_distance: 最大步行距离（米），默认1300
        subway_search_radius: 地铁站搜索半径（米），默认1500
        subway_keywords: 地铁站搜索关键词，默认"地铁站"
        max_subway_walking_seconds: 到最近地铁站最大步行时间（秒），默认900（15分钟）
        friend_start_address: 朋友起点地址，默认"合肥火车站"
        friend_start_city: 朋友起点城市，默认"合肥"
        min_drive_faster_seconds: 朋友开车比步行至少快多少秒，默认480（8分钟）
        atm_search_radius: ATM 搜索半径（米），默认300
        atm_keywords: ATM 搜索关键词，默认"ATM"

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 附近2000米范围验证
    # 注意：首个约束应该为"你想找一个附近指定距离的poi点"，而非"你想找一个离你不超过指定距离的poi点"
    print(f"【步骤1】验证附近范围（{search_radius}米范围内，关键词：{keywords}）")
    print("-" * 80)
    around_search_result = maps_around_search(
        location=user_location,
        radius=str(search_radius),
        keywords=keywords
    )
    if around_search_result.error:
        print(f"❌ 搜索附近POI失败: {around_search_result.error}")
        return False

    if not around_search_result.pois:
        print(f"❌ 未找到符合条件的POI")
        return False

    poi_found = False
    for poi in around_search_result.pois:
        if poi.id == poi_id:
            poi_found = True
            print(f"✅ 在{search_radius}米范围内找到目标POI: {poi.name} (ID: {poi_id})")
            break

    if not poi_found:
        print(f"❌ 目标POI {poi_id} 不在{search_radius}米范围内的{keywords}列表中")
        return False

    # 步骤2: 你步行距离≤1300米
    print(f"\n【步骤2】验证你步行到电竞馆距离（≤{max_walking_distance}米）")
    print("-" * 80)
    poi_detail = maps_search_detail(id=poi_id)
    if poi_detail.error:
        print(f"❌ 获取POI详情失败: {poi_detail.error}")
        return False

    if not poi_detail.location:
        print(f"❌ POI详情中没有location信息")
        return False

    venue_location = poi_detail.location
    print(f"✅ 获取电竞馆坐标: {venue_location} ({poi_detail.name})")

    walking_result = maps_walking_by_coordinates(
        origin=user_location,
        destination=venue_location
    )
    if walking_result.error:
        print(f"❌ 计算步行路线失败: {walking_result.error}")
        return False

    if walking_result.total_distance_meters is None:
        print(f"❌ 无法获取步行距离")
        return False

    walking_distance = walking_result.total_distance_meters
    if walking_distance > max_walking_distance:
        print(f"❌ 步行距离{walking_distance}米，超过{max_walking_distance}米")
        return False
    print(f"✅ 步行距离{walking_distance}米，符合要求（≤{max_walking_distance}米）")

    # 步骤3: 最近地铁站步行≤15分钟（且地铁站在电竞馆1500米范围内）
    print(f"\n【步骤3】验证电竞馆到最近地铁站步行时间（≤{max_subway_walking_seconds}秒，即{max_subway_walking_seconds // 60}分钟，地铁站在{subway_search_radius}米范围内）")
    print("-" * 80)
    subway_search_result = maps_around_search(
        location=venue_location,
        radius=str(subway_search_radius),
        keywords=subway_keywords
    )
    if subway_search_result.error:
        print(f"❌ 搜索地铁站失败: {subway_search_result.error}")
        return False

    if not subway_search_result.pois or len(subway_search_result.pois) == 0:
        print(f"❌ 电竞馆{subway_search_radius}米范围内未找到地铁站")
        return False

    print(f"✅ 找到{len(subway_search_result.pois)}个地铁站")

    min_walking_duration = None
    for subway_station in subway_search_result.pois:
        sub_walking_result = maps_walking_by_coordinates(
            origin=venue_location,
            destination=subway_station.location
        )
        if sub_walking_result.error:
            print(f"⚠️  计算到地铁站{subway_station.name}的步行路线失败: {sub_walking_result.error}")
            continue

        if sub_walking_result.total_duration_seconds is None:
            print(f"⚠️  无法获取到地铁站{subway_station.name}的步行时长")
            continue

        duration = sub_walking_result.total_duration_seconds
        if min_walking_duration is None or duration < min_walking_duration:
            min_walking_duration = duration
            print(f"  到地铁站{subway_station.name}的步行时长: {duration}秒")

    if min_walking_duration is None:
        print(f"❌ 无法计算到任何地铁站的步行时长")
        return False

    if min_walking_duration > max_subway_walking_seconds:
        print(f"❌ 到最近地铁站步行时长{min_walking_duration}秒，超过{max_subway_walking_seconds}秒（{max_subway_walking_seconds // 60}分钟）")
        return False
    print(f"✅ 到最近地铁站步行时长{min_walking_duration}秒，符合要求（≤{max_subway_walking_seconds}秒）")

    # 步骤4: 朋友（合肥火车站）开车比你步行至少快8分钟
    print(f"\n【步骤4】验证朋友开车比你步行至少快{min_drive_faster_seconds // 60}分钟")
    print("-" * 80)
    friend_geo_result = maps_geo(address=friend_start_address, city=friend_start_city)
    if friend_geo_result.error:
        print(f"❌ 获取朋友起点坐标失败: {friend_geo_result.error}")
        return False

    if not friend_geo_result.results or len(friend_geo_result.results) == 0:
        print(f"❌ 未找到朋友起点地址")
        return False

    friend_origin = friend_geo_result.results[0].location
    print(f"✅ 朋友起点坐标: {friend_origin} ({friend_geo_result.results[0].formatted_address})")

    drive_result = maps_driving_by_coordinates(
        origin=friend_origin,
        destination=venue_location
    )
    if drive_result.error:
        print(f"❌ 计算朋友驾车路线失败: {drive_result.error}")
        return False

    if drive_result.total_duration_seconds is None:
        print(f"❌ 无法获取朋友驾车时长")
        return False

    t_drive = drive_result.total_duration_seconds
    print(f"✅ 朋友驾车时长: {t_drive}秒")

    user_walking_result = maps_walking_by_coordinates(
        origin=user_location,
        destination=venue_location
    )
    if user_walking_result.error:
        print(f"❌ 计算你步行路线失败: {user_walking_result.error}")
        return False

    if user_walking_result.total_duration_seconds is None:
        print(f"❌ 无法获取你步行时长")
        return False

    t_walk = user_walking_result.total_duration_seconds
    print(f"✅ 你步行时长: {t_walk}秒")

    diff = t_walk - t_drive
    if diff < min_drive_faster_seconds:
        print(f"❌ 步行比驾车多{diff}秒，不满足至少多{min_drive_faster_seconds}秒（{min_drive_faster_seconds // 60}分钟）")
        return False
    print(f"✅ 步行比驾车多{diff}秒，符合要求（≥{min_drive_faster_seconds}秒）")

    # 步骤5: 电竞馆300米内有ATM
    print(f"\n【步骤5】验证电竞馆{atm_search_radius}米内有ATM")
    print("-" * 80)
    atm_search_result = maps_around_search(
        location=venue_location,
        radius=str(atm_search_radius),
        keywords=atm_keywords
    )
    if atm_search_result.error:
        print(f"❌ 搜索ATM失败: {atm_search_result.error}")
        return False

    if not atm_search_result.pois or len(atm_search_result.pois) == 0:
        print(f"❌ 电竞馆{atm_search_radius}米范围内未找到ATM")
        return False

    print(f"✅ 找到ATM: {atm_search_result.pois[0].name} (共{len(atm_search_result.pois)}个)")

    print(f"\n✅ 所有验证通过！")
    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python 756.py <poi_id> [user_location]")
        print("示例: python 756.py B0LDD7HSX7")
        print("示例: python 756.py B0LDD7HSX7 117.285236,31.872469")
        print("未传参，使用示例默认值运行。")
        poi_id = "B0LDD7HSX7"
        user_location = "117.285236,31.872469"
    else:
        poi_id = sys.argv[1]
        user_location = sys.argv[2] if len(sys.argv) > 2 else "117.285236,31.872469"
        

    print(f"开始验证POI: {poi_id}")
    print(f"用户坐标: {user_location}")
    print("=" * 80)

    result = verify_poi(poi_id, user_location=user_location)

    print("=" * 80)
    print(f"验证结果: {'通过' if result else '失败'}")
