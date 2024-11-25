import streamlit as st
import pandas as pd
import hashlib
import os

# CSV 파일 로드 및 저장 함수
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("movie_data.csv", encoding='cp949')
        df.columns = df.columns.str.strip().str.lower()
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

# 비밀번호 해시 함수
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# 메인 앱 함수
def main():
    st.set_page_config(page_title="영화 추천 시스템", layout="wide")
    st.title("🎬 영화 추천 및 관리 시스템")

    # 데이터 로드
    df = load_data()
    users = load_users()
    ratings = load_ratings()

    # 관리자 계정 설정
    ADMIN_CREDENTIALS = {'username': 'admin', 'password': hash_password('admin123')}

    # 세션 상태 초기화
    if 'user' not in st.session_state:
        st.session_state.user = None
        st.session_state.is_admin = False

    # 포스터 폴더 경로
    poster_folder = "poster_file"

    # 사이드바 사용자 인증
    with st.sidebar:
        st.header("👤 사용자 인증")
        if st.session_state.user:
            st.write(f"환영합니다, **{st.session_state.user}님!**")
            if st.session_state.is_admin:
                st.warning("관리자 모드 활성화")
            if st.button("로그아웃"):
                st.session_state.user = None
                st.session_state.is_admin = False
                st.success("로그아웃 성공!")
        else:
            choice = st.radio("로그인/회원가입", ["로그인", "회원가입"])
            if choice == "로그인":
                username = st.text_input("사용자명")
                password = st.text_input("비밀번호", type="password")
                if st.button("로그인"):
                    if username == ADMIN_CREDENTIALS['username'] and hash_password(password) == ADMIN_CREDENTIALS['password']:
                        st.session_state.user = username
                        st.session_state.is_admin = True
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

    # 메인 영역 탭
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📚 영화 검색", "⭐ 추천 영화", "📈 나의 활동", "⚙️ 회원 관리", "📊 관리자 보기"])

    # 영화 검색
    with tab1:
        st.header("🎥 영화 검색")
        search_term = st.text_input("🔍 검색", placeholder="영화 제목을 입력하세요...")
        genre_filter = st.selectbox("🎭 장르 필터", options=["모든 장르"] + df['genre'].unique().tolist())

        # 검색 결과 필터링
        filtered_df = df[df['title'].str.contains(search_term, case=False)]
        if genre_filter != "모든 장르":
            filtered_df = filtered_df[filtered_df['genre'] == genre_filter]

        if len(filtered_df) == 0:
            st.warning("검색 결과가 없습니다.")
        else:
            for _, movie in filtered_df.iterrows():
                st.subheader(movie['title'])
                st.write(f"**장르**: {movie['genre']}")
                st.write(f"**평점**: {movie['rating']}")
                st.markdown("---")

    # 추천 영화
    with tab2:
        st.header("⭐ 추천 영화")
        if st.session_state.user:
            user_ratings = [r for r in ratings if r['username'] == st.session_state.user]
            if user_ratings:
                favorite_genres = [df[df['title'] == r['movie']].iloc[0]['genre'] for r in user_ratings if not df[df['title'] == r['movie']].empty]
                recommended_movies = df[df['genre'].isin(favorite_genres) & ~df['title'].isin([r['movie'] for r in user_ratings])]
                for _, movie in recommended_movies.head(5).iterrows():
                    st.subheader(movie['title'])
                    st.write(f"**장르**: {movie['genre']}")
                    st.write(f"**평점**: {movie['rating']}")
                    st.markdown("---")
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
                    new_rating = st.number_input(f"평점 수정 ({activity['movie']})", value=activity['rating'], min_value=0.0, max_value=10.0, step=0.1)
                    new_review = st.text_area(f"리뷰 수정 ({activity['movie']})", value=activity.get('review', ''))
                    if st.button(f"'{activity['movie']}' 수정"):
                        activity['rating'] = new_rating
                        activity['review'] = new_review
                        save_ratings(ratings)
                        st.success(f"'{activity['movie']}'에 대한 수정이 완료되었습니다.")
                    st.markdown("---")
            else:
                st.info("아직 활동 내역이 없습니다.")
        else:
            st.info("로그인 후 활동 내역을 확인할 수 있습니다.")

    # 회원 관리
    with tab4:
        st.header("⚙️ 회원 관리")
        if st.session_state.user:
            if st.session_state.is_admin:
                st.subheader("👥 모든 사용자 관리 (관리자 전용)")
                for user in users:
                    st.write(f"**사용자명**: {user['username']}")
                    if st.button(f"삭제 ({user['username']})"):
                        users = [u for u in users if u['username'] != user['username']]
                        save_users(users)
                        st.success(f"사용자 '{user['username']}'가 삭제되었습니다.")
                st.markdown("---")
            else:
                st.subheader("🛠️ 내 계정 수정")
                new_username = st.text_input("새 사용자명", value=st.session_state.user)
                new_password = st.text_input("새 비밀번호", type="password")
                if st.button("계정 수정"):
                    for user in users:
                        if user['username'] == st.session_state.user:
                            user['username'] = new_username
                            user['password'] = hash_password(new_password)
                            st.session_state.user = new_username
                            save_users(users)
                            st.success("계정 정보가 수정되었습니다.")

    # 관리자 보기
    with tab5:
        st.header("📊 관리자 보기")
        if st.session_state.is_admin:
            st.subheader("모든 사용자 정보")
            st.write(pd.DataFrame(users))

            st.subheader("모든 평점 및 리뷰")
            st.write(pd.DataFrame(ratings))
        else:
            st.info("관리자 권한이 필요합니다.")

if __name__ == "__main__":
    main()
