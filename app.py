import streamlit as st
import pandas as pd
import hashlib
import os

# 관리자 계정 설정
ADMIN_CREDENTIALS = {'username': 'admin', 'password': hashlib.sha256('admin123'.encode()).hexdigest()}

# 데이터 로드 및 저장 함수
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("movie_data.csv", encoding='cp949')
        df.columns = df.columns.str.strip().str.lower()  # 컬럼명 공백 제거 및 소문자화
        return df
    except Exception as e:
        st.error(f"데이터 로드 오류: {e}")
        return pd.DataFrame()

def save_users(users):
    pd.DataFrame(users).to_csv("movie_users.csv", index=False, encoding='cp949')

def load_users():
    path = "movie_users.csv"
    if os.path.exists(path):
        return pd.read_csv(path, encoding='cp949').to_dict('records')
    return []

def save_ratings(ratings):
    pd.DataFrame(ratings).to_csv("movie_ratings.csv", index=False, encoding='cp949')

def load_ratings():
    path = "movie_ratings.csv"
    if os.path.exists(path):
        return pd.read_csv(path, encoding='cp949').to_dict('records')
    return []

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def main():
    st.set_page_config(page_title="영화 추천 시스템", layout="wide")
    st.title("🎬 영화 추천 및 검색 시스템")

    df = load_data()
    users = load_users()
    ratings = load_ratings()

    if 'user' not in st.session_state:
        st.session_state.user = None

    # 포스터 파일 폴더 경로
    poster_folder = "poster_file"

    # 사이드바 사용자 인증
    with st.sidebar:
        st.header("👤 사용자 인증")
        if st.session_state.user:
            st.write(f"환영합니다, **{st.session_state.user}님!**")
            if st.button("로그아웃"):
                st.session_state.user = None
                st.success("로그아웃 성공!")
        else:
            choice = st.radio("로그인/회원가입", ["로그인", "회원가입"])
            if choice == "로그인":
                username = st.text_input("사용자명")
                password = st.text_input("비밀번호", type="password")
                if st.button("로그인"):
                    if username == ADMIN_CREDENTIALS['username'] and hash_password(password) == ADMIN_CREDENTIALS['password']:
                        st.session_state.user = "관리자"
                        st.success("관리자로 로그인 성공!")
                    else:
                        user = next((u for u in users if u['username'] == username and u['password'] == hash_password(password)), None)
                        if user:
                            st.session_state.user = username
                            st.success("로그인 성공!")
                        else:
                            st.error("잘못된 사용자명 또는 비밀번호입니다.")
            else:
                new_username = st.text_input("새 사용자명")
                new_password = st.text_input("새 비밀번호", type="password")
                if st.button("회원가입"):
                    if any(u['username'] == new_username for u in users):
                        st.error("이미 존재하는 사용자명입니다.")
                    else:
                        users.append({'username': new_username, 'password': hash_password(new_password)})
                        save_users(users)
                        st.success("회원가입 성공! 이제 로그인할 수 있습니다.")

    st.markdown("---")

    # 탭 구성
    tab1, tab2, tab3, tab4 = st.tabs(["📚 영화 검색", "⭐ 추천 영화", "📈 나의 활동", "🛠 관리자"])

    # 영화 검색
    with tab1:
        st.header("🎥 영화 검색")
        search_term = st.text_input("🔍 검색", placeholder="영화 제목을 입력하세요...")
        genre_filter = st.selectbox("🎭 장르 필터", options=["모든 장르"] + df['genre'].unique().tolist())

        # 필터링 및 페이지네이션
        filtered_df = df[df['title'].str.contains(search_term, case=False)]
        if genre_filter != "모든 장르":
            filtered_df = filtered_df[filtered_df['genre'] == genre_filter]

        total_movies = len(filtered_df)
        if total_movies == 0:
            st.warning("검색 결과가 없습니다.")
        else:
            page_size = 5
            total_pages = (total_movies // page_size) + (1 if total_movies % page_size != 0 else 0)
            page = st.number_input("페이지 번호", min_value=1, max_value=total_pages, value=1)

            start_idx = (page - 1) * page_size
            end_idx = min(page * page_size, total_movies)

            for _, movie in filtered_df.iloc[start_idx:end_idx].iterrows():
                st.subheader(movie['title'])

                # 포스터 파일 경로
                poster_path = os.path.join(poster_folder, movie.get('poster_file', ''))
                if os.path.exists(poster_path) and pd.notna(movie.get('poster_file')):
                    st.image(poster_path, width=200)  # 이미지 표시
                else:
                    st.write("포스터 이미지가 없습니다.")  # 이미지가 없을 경우 메시지 출력

                # 영화 정보 출력
                st.write(f"**영화 ID**: {movie['movie_id']}")
                st.write(f"**제작사**: {movie['distributor']}")
                st.write(f"**감독**: {movie['director']}")
                st.write(f"**배우**: {movie['actor']}")
                st.write(f"**장르**: {movie['genre']}")
                st.write(f"**개봉일**: {movie['release_date']}")
                st.write(f"**상영 시간**: {movie['running_time']}분")
                st.write(f"**영화 평점**: {movie['rating']}")
                st.write(f"**현재 상태**: {movie['running_state']}")
                st.markdown("---")

    # 추천 영화
    with tab2:
        st.header("⭐ 추천 영화")
        if st.session_state.user:
            user_ratings = [r for r in ratings if r['username'] == st.session_state.user]
            if user_ratings:
                favorite_genres = [df[df['title'] == r['movie']].iloc[0]['genre'] for r in user_ratings if not df[df['title'] == r['movie']].empty]
                recommended_movies = df[df['genre'].isin(favorite_genres) & ~df['title'].isin([r['movie'] for r in user_ratings])]
                if not recommended_movies.empty:
                    for _, movie in recommended_movies.head(5).iterrows():
                        st.subheader(movie['title'])
                        st.write(f"**장르**: {movie['genre']}")
                        st.write(f"**평점**: {movie['rating']}")
                        st.markdown("---")
                else:
                    st.info("추천할 영화가 없습니다. 더 많은 평점을 남겨보세요!")
            else:
                st.info("평점을 남긴 영화가 없습니다. 추천을 위해 영화에 평점을 남겨보세요!")
        else:
            st.info("로그인 후 추천 영화를 확인할 수 있습니다.")

    # 나의 활동
    with tab3:
        st.header("📈 나의 활동")
        if st.session_state.user:
            user_activity = [r for r in ratings if r['username'] == st.session_state.user]
            if user_activity:
                for activity in user_activity:
                    st.subheader(activity['movie'])
                    st.write(f"**평점**: {activity['rating']}")
                    if activity.get('review'):
                        st.write(f"**리뷰**: {activity['review']}")
                    if st.button(f"{activity['movie']} 수정", key=f"edit-{activity['movie']}"):
                        new_rating = st.number_input("수정할 평점 입력", min_value=0.0, max_value=10.0, value=activity['rating'], step=0.1)
                        new_review = st.text_area("수정할 리뷰 입력", value=activity.get('review', ''))
                        if st.button(f"{activity['movie']} 수정 저장", key=f"save-edit-{activity['movie']}"):
                            activity['rating'] = new_rating
                            activity['review'] = new_review
                            save_ratings(ratings)
                            st.success("수정 완료!")
                    st.markdown("---")
            else:
                st.info("아직 활동 내역이 없습니다.")
        else:
            st.info("로그인 후 활동 내역을 확인할 수 있습니다.")

    # 관리자 영역
    with tab4:
        st.header("🛠 관리자")
        if st.session_state.user == "관리자":
            st.subheader("사용자 관리")
            for user in users:
                st.write(f"**사용자명**: {user['username']}")
                if st.button(f"{user['username']} 삭제", key=f"delete-{user['username']}"):
                    users = [u for u in users if u['username'] != user['username']]
                    save_users(users)
                    st.success(f"사용자 {user['username']} 삭제 완료!")
            st.markdown("---")
            st.subheader("영화 리뷰 관리")
            for rating in ratings:
                st.write(f"**영화 제목**: {rating['movie']}")
                st.write(f"**작성자**: {rating['username']}")
                st.write(f"**평점**: {rating['rating']}")
                st.write(f"**리뷰**: {rating.get('review', '없음')}")
                if st.button(f"{rating['movie']} 리뷰 삭제", key=f"delete-{rating['movie']}"):
                    ratings = [r for r in ratings if r != rating]
                    save_ratings(ratings)
                    st.success(f"{rating['movie']} 리뷰 삭제 완료!")
            st.markdown("---")
        else:
            st.warning("관리자 권한이 필요합니다.")
