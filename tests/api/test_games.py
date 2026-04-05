import httpx
import pytest

pytestmark = pytest.mark.usefixtures("_clean_tables")


async def _register(client: httpx.AsyncClient, username: str) -> dict:
    resp = await client.post(
        "/register",
        json={"username": username, "password": "password123"},
    )
    assert resp.status_code == 201
    return resp.json()


async def _auth_header(client: httpx.AsyncClient, username: str) -> dict[str, str]:
    tokens = await _register(client, username)
    return {"Authorization": f"Bearer {tokens['access_token']}"}


async def _create_game(client: httpx.AsyncClient, headers: dict[str, str]) -> dict:
    resp = await client.post("/games", headers=headers)
    assert resp.status_code == 201
    return resp.json()


async def _join_game(
    client: httpx.AsyncClient,
    game_id: str,
    headers: dict[str, str],
) -> dict:
    resp = await client.post(f"/games/{game_id}/join", headers=headers)
    assert resp.status_code == 200
    return resp.json()


# --- POST /games ---


async def test_create_game(app_client: httpx.AsyncClient):
    h = await _auth_header(app_client, "creator1")
    game = await _create_game(app_client, h)
    assert game["status"] == "waiting"
    assert game["player1"]["username"] == "creator1"
    assert game["player2"] is None
    assert game["winner"] is None


async def test_create_game_unauthenticated(app_client: httpx.AsyncClient):
    resp = await app_client.post("/games")
    assert resp.status_code == 401


# --- POST /games/{id}/join ---


async def test_join_game(app_client: httpx.AsyncClient):
    h1 = await _auth_header(app_client, "joiner_p1")
    h2 = await _auth_header(app_client, "joiner_p2")
    game = await _create_game(app_client, h1)

    joined = await _join_game(app_client, game["id"], h2)
    assert joined["status"] == "in_progress"
    assert joined["player1"]["username"] == "joiner_p1"
    assert joined["player2"]["username"] == "joiner_p2"


async def test_join_own_game(app_client: httpx.AsyncClient):
    h = await _auth_header(app_client, "selfjoin")
    game = await _create_game(app_client, h)

    resp = await app_client.post(f"/games/{game['id']}/join", headers=h)
    assert resp.status_code == 409
    assert "own game" in resp.json()["detail"].lower()


async def test_join_already_started_game(app_client: httpx.AsyncClient):
    h1 = await _auth_header(app_client, "started_p1")
    h2 = await _auth_header(app_client, "started_p2")
    h3 = await _auth_header(app_client, "started_p3")
    game = await _create_game(app_client, h1)
    await _join_game(app_client, game["id"], h2)

    resp = await app_client.post(f"/games/{game['id']}/join", headers=h3)
    assert resp.status_code == 409


async def test_join_nonexistent_game(app_client: httpx.AsyncClient):
    h = await _auth_header(app_client, "joiner_noexist")
    resp = await app_client.post("/games/00000000000000000000000000/join", headers=h)
    assert resp.status_code == 404


# --- POST /games/{id}/moves ---


async def test_play_move(app_client: httpx.AsyncClient):
    h1 = await _auth_header(app_client, "move_p1")
    h2 = await _auth_header(app_client, "move_p2")
    game = await _create_game(app_client, h1)
    await _join_game(app_client, game["id"], h2)

    resp = await app_client.post(
        f"/games/{game['id']}/moves",
        json={"column": 3},
        headers=h1,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["column"] == 3
    assert data["move_number"] == 1
    assert data["player"]["username"] == "move_p1"


async def test_play_wrong_turn(app_client: httpx.AsyncClient):
    h1 = await _auth_header(app_client, "turn_p1")
    h2 = await _auth_header(app_client, "turn_p2")
    game = await _create_game(app_client, h1)
    await _join_game(app_client, game["id"], h2)

    # Player 2 tries to go first
    resp = await app_client.post(
        f"/games/{game['id']}/moves",
        json={"column": 0},
        headers=h2,
    )
    assert resp.status_code == 409
    assert "not your turn" in resp.json()["detail"].lower()


async def test_play_column_full(app_client: httpx.AsyncClient):
    h1 = await _auth_header(app_client, "full_p1")
    h2 = await _auth_header(app_client, "full_p2")
    game = await _create_game(app_client, h1)
    await _join_game(app_client, game["id"], h2)

    # Fill column 0 (6 moves alternating)
    headers = [h1, h2]
    for i in range(6):
        resp = await app_client.post(
            f"/games/{game['id']}/moves",
            json={"column": 0},
            headers=headers[i % 2],
        )
        assert resp.status_code == 201

    # 7th move in column 0 should fail
    resp = await app_client.post(
        f"/games/{game['id']}/moves",
        json={"column": 0},
        headers=h1,
    )
    assert resp.status_code == 422


async def test_play_invalid_column(app_client: httpx.AsyncClient):
    h1 = await _auth_header(app_client, "invcol_p1")
    h2 = await _auth_header(app_client, "invcol_p2")
    game = await _create_game(app_client, h1)
    await _join_game(app_client, game["id"], h2)

    resp = await app_client.post(
        f"/games/{game['id']}/moves",
        json={"column": 7},
        headers=h1,
    )
    assert resp.status_code == 422


async def test_play_on_waiting_game(app_client: httpx.AsyncClient):
    h1 = await _auth_header(app_client, "wait_p1")
    game = await _create_game(app_client, h1)

    resp = await app_client.post(
        f"/games/{game['id']}/moves",
        json={"column": 0},
        headers=h1,
    )
    assert resp.status_code == 409


async def test_play_winning_move(app_client: httpx.AsyncClient):
    h1 = await _auth_header(app_client, "win_p1")
    h2 = await _auth_header(app_client, "win_p2")
    game = await _create_game(app_client, h1)
    await _join_game(app_client, game["id"], h2)

    # P1 plays col 0, P2 plays col 1, repeat — P1 gets 4 in col 0
    headers = [h1, h2]
    moves = [0, 1, 0, 1, 0, 1]
    for i, col in enumerate(moves):
        await app_client.post(
            f"/games/{game['id']}/moves",
            json={"column": col},
            headers=headers[i % 2],
        )

    # P1 plays col 0 for the win (4th in column 0)
    resp = await app_client.post(
        f"/games/{game['id']}/moves",
        json={"column": 0},
        headers=h1,
    )
    assert resp.status_code == 201

    # Verify game is won
    detail = await app_client.get(f"/games/{game['id']}", headers=h1)
    data = detail.json()
    assert data["status"] == "won"
    assert data["winner"]["username"] == "win_p1"
    assert data["current_player"] is None


async def test_play_after_game_over(app_client: httpx.AsyncClient):
    h1 = await _auth_header(app_client, "over_p1")
    h2 = await _auth_header(app_client, "over_p2")
    game = await _create_game(app_client, h1)
    await _join_game(app_client, game["id"], h2)

    # P1 wins vertically in col 0
    moves = [0, 1, 0, 1, 0, 1, 0]
    headers = [h1, h2]
    for i, col in enumerate(moves):
        await app_client.post(
            f"/games/{game['id']}/moves",
            json={"column": col},
            headers=headers[i % 2],
        )

    # Try another move after game over
    resp = await app_client.post(
        f"/games/{game['id']}/moves",
        json={"column": 2},
        headers=h2,
    )
    assert resp.status_code == 409


# --- GET /games/{id} ---


async def test_get_game_detail(app_client: httpx.AsyncClient):
    h1 = await _auth_header(app_client, "detail_p1")
    h2 = await _auth_header(app_client, "detail_p2")
    game = await _create_game(app_client, h1)
    await _join_game(app_client, game["id"], h2)

    # Play a move
    await app_client.post(
        f"/games/{game['id']}/moves",
        json={"column": 3},
        headers=h1,
    )

    resp = await app_client.get(f"/games/{game['id']}", headers=h1)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "in_progress"
    assert data["current_player"] == 2
    board = data["board"]
    assert len(board) == 6
    assert all(len(row) == 7 for row in board)
    # Bottom row, column 3 should have player 1's piece
    assert board[5][3] == 1


async def test_get_game_not_found(app_client: httpx.AsyncClient):
    h = await _auth_header(app_client, "notfound_user")
    resp = await app_client.get("/games/00000000000000000000000000", headers=h)
    assert resp.status_code == 404


async def test_get_game_unauthenticated(app_client: httpx.AsyncClient):
    resp = await app_client.get("/games/someid")
    assert resp.status_code == 401


# --- GET /games/{id}/moves ---


async def test_get_moves(app_client: httpx.AsyncClient):
    h1 = await _auth_header(app_client, "getmoves_p1")
    h2 = await _auth_header(app_client, "getmoves_p2")
    game = await _create_game(app_client, h1)
    await _join_game(app_client, game["id"], h2)

    await app_client.post(f"/games/{game['id']}/moves", json={"column": 0}, headers=h1)
    await app_client.post(f"/games/{game['id']}/moves", json={"column": 1}, headers=h2)

    resp = await app_client.get(f"/games/{game['id']}/moves", headers=h1)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    assert data[0]["move_number"] == 1
    assert data[0]["column"] == 0
    assert data[1]["move_number"] == 2
    assert data[1]["column"] == 1


async def test_get_moves_empty(app_client: httpx.AsyncClient):
    h1 = await _auth_header(app_client, "emptymoves_p1")
    game = await _create_game(app_client, h1)

    resp = await app_client.get(f"/games/{game['id']}/moves", headers=h1)
    assert resp.status_code == 200
    assert resp.json() == []


# --- GET /games (list with pagination) ---


async def test_list_games(app_client: httpx.AsyncClient):
    h = await _auth_header(app_client, "listgames_user")
    await _create_game(app_client, h)
    await _create_game(app_client, h)

    resp = await app_client.get("/games", headers=h)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["games"]) == 2
    assert data["next_cursor"] is None


async def test_list_games_pagination(app_client: httpx.AsyncClient):
    h = await _auth_header(app_client, "paguser")
    for _ in range(3):
        await _create_game(app_client, h)

    # Request with limit=2
    resp = await app_client.get("/games?limit=2", headers=h)
    data = resp.json()
    assert len(data["games"]) == 2
    assert data["next_cursor"] is not None

    # Next page
    resp2 = await app_client.get(
        f"/games?limit=2&cursor={data['next_cursor']}", headers=h
    )
    data2 = resp2.json()
    assert len(data2["games"]) == 1
    assert data2["next_cursor"] is None

    # No overlap
    ids_page1 = {g["id"] for g in data["games"]}
    ids_page2 = {g["id"] for g in data2["games"]}
    assert ids_page1.isdisjoint(ids_page2)


async def test_list_games_empty(app_client: httpx.AsyncClient):
    h = await _auth_header(app_client, "emptygames_user")
    resp = await app_client.get("/games", headers=h)
    assert resp.status_code == 200
    data = resp.json()
    assert data["games"] == []
    assert data["next_cursor"] is None


async def test_list_games_unauthenticated(app_client: httpx.AsyncClient):
    resp = await app_client.get("/games")
    assert resp.status_code == 401
