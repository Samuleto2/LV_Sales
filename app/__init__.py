from flask import Flask, render_template
from app.config import Config
from app.extensions import db, migrate, cors

def create_app():
    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static"
    )

    app.config.from_object(Config)

    cors.init_app(app)
    db.init_app(app)
    migrate.init_app(app, db)

    from app.routes.customers import customers_bp
    from app.routes.sales import sales_bp
    from app.routes.pdf_routes import pdf_bp

    app.register_blueprint(customers_bp)
    app.register_blueprint(sales_bp)
    app.register_blueprint(pdf_bp)

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/sales/explore")
    def explore_sales():
        from app.models.sale import Sale
        from app.models.customer import Customer

        sales = (
            Sale.query
            .join(Customer)
            .order_by(Sale.created_at.desc())
            .limit(50)
            .all()
        )
        return render_template("explore_sales.html", sales=sales)

    @app.route("/proximamente")
    def proximamente_view():
        return render_template("proximamente.html")

    return app