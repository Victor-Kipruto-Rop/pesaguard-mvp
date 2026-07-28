from app.exceptions.models import GatewayErrorCode, ProblemDetails


def test_problem_details_from_exception_includes_request_metadata():
    problem = ProblemDetails.from_exception(
        status=400,
        code=GatewayErrorCode.FORBIDDEN.value,
        title="Forbidden",
        detail="Access to this resource is denied",
        request_id="request-123",
        instance="/api/v1/payments",
        errors=[{"field": "amount", "message": "required"}],
    )

    assert problem.status == 400
    assert problem.code == GatewayErrorCode.FORBIDDEN.value
    assert problem.title == "Forbidden"
    assert problem.detail == "Access to this resource is denied"
    assert problem.request_id == "request-123"
    assert problem.instance == "/api/v1/payments"
    assert problem.errors == [{"field": "amount", "message": "required"}]


def test_unknown_service_response_uses_problem_details_format(client, settings):
    from app.core.security import issue_development_token

    token = issue_development_token("test", settings)
    response = client.get("/api/v1/unknown", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 404
    body = response.json()
    assert "error" in body
    error = body["error"]
    assert error["code"] == GatewayErrorCode.NOT_FOUND.value
    assert error["title"] == "Not Found"
    assert error["status"] == 404
    assert error["detail"] == "Not Found"
    assert "request_id" in error
