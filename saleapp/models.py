from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from saleapp import db
from datetime import datetime
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))



class BaseModel(db.Model):
    __abstract__= True
    
    id = Column(Integer, primary_key=True, autoincrement=True)



class Category(BaseModel):
    __tablename__ = 'category'
    
    name = Column(String(20), nullable=False)
    product = relationship('Product', backref='category', lazy=True)
    
    def __str__(self):
        return self.name
    
    
    
class Product(BaseModel):
    __tablename__ = 'product'
    
    name = Column(String(50), nullable=False)
    description = Column(String(266))
    price = Column(Float, default=0)
    image = Column(String(100))
    active = Column(Boolean, default=True)
    created_date = Column(DateTime, default=datetime.now())
    category_id = Column(Integer, ForeignKey(Category.id), nullable=False)
    
    def __str__(self):
        return self.name
    
if __name__ == '__main__':
    
    Product.query.delete()
    Category.query.delete()
    db.session.commit()
    
    categories = [
    Category(name='Mobile'),     
    Category(name='Laptop'),     
    Category(name='Tablet'),     
    Category(name='Monitor'),    
    Category(name='Watch'),      
    ]

    for c in categories:
        db.session.add(c)
    db.session.commit()

    
    products = [
        {
            "id": 1,
            "name": "iPhone 16 Pro Max",
            "price": 37000000,
            "description": "Apple, 512GB, RAM: 8GB, iOS18",
            "image": "image/p1.jpg",
            "category_id": 1
        },
        {
            "id": 2,
            "name": "iPad Pro M1",
            "price": 36000000,
            "description": "Apple, 256GB, RAM: 8GB, Wifi",
            "image": "image/p2.jpg",
            "category_id": 3
        },
        {
            "id": 3,
            "name": "Apple Watch series 10",
            "price": 15000000,
            "description": "Apple S10 chip, RAM: 64GB, WatchOS 11",
            "image": "image/p3.jpg",
            "category_id": 5
        },
        {
            "id": 4,
            "name": "Macbook Pro M4",
            "price": 39000000,
            "description": "Apple M4 chip, RAM: 12GB, SSD: 512GB",
            "image": "image/p4.jpg",
            "category_id": 2
        },
        {
            "id": 5,
            "name": "Lenovo LOQ 2024",
            "price": 18000000,
            "description": "Intel core i5-13450HX, Gefore RTX2050, RAM: 12GB, SSD: 512",
            "image": "image/p5.jpg",
            "category_id": 2
        },
        {
            "id": 6,
            "name": "Acer Nitro V",
            "price": 17000000,
            "description": "Intel core i5-13420H, Gefore RTX2050, RAM: 16GB, SSD: 512",
            "image": "image/p6.jpg",
            "category_id": 2
        },
        {
            "id": 7,
            "name": "Asus TUF",
            "price": 3000000,
            "description": "24inches, FHD, 99%sRGB, IPS, 180HZ",
            "image": "image/p7.jpg",
            "category_id": 4
        },
        {
            "id": 8,
            "name": "Samsung Odyssey",
            "price": 6000000,
            "description": "27inches, 2K, IPS, 180HZ",
            "image": "image/p8.jpg",
            "category_id": 4

        },
        {
            "id": 9,
            "name": "Iphone 7 Plus",
            "price": 5000000.0,
            "description": "Apple, RAM: 4GB,  256GB, iOS15",
            "image": "image/p9.jpg",
            "category_id": 1
        },
        {
            "id": 10,
            "name": "Iphone XS Max",
            "price": 10000000.0,
            "description": "Apple, RAM: 4GB,  256GB, iOS16",
            "image": "image/p10.jpg",
            "category_id": 1
        },
        {
            "id": 11,
            "name": "iPad Air M1",
            "price": 15000000.0,
            "description": "Apple, RAM: 8GB,  512GB, ipadOS16",
            "image": "image/p11.jpg",
            "category_id": 3
        },
        {
            "id": 13,
            "name": "MSI GF63 Thin",
            "price": 15000000.0,
            "description": "MSI,I5-12450H, RAM: 8GB, SSD, 512GB , RTX2050",
            "image": "image/13.jpg",
            "category_id": 2

        },
        {
            "id": 14,
            "name": "Legion 7",
            "price": 60000000.0,
            "description": "Lenovo, i9-14900HX, RAM: 32GB, SSD: 512GB, RTX4070",
            "image": "image/14.jpg",
            "category_id": 2
        },
        {
            "id": 15,
            "name": "Legion 7",
            "price": 60000000.0,
            "description": "Lenovo, i9-14900HX, RAM: 32GB, SSD: 512GB, RTX4070",
            "image": "image/15.jpg",
            "category_id": 2
        }
    ]
    
    for p in products:
        pro = Product(name=p['name'], 
                      price=p['price'], 
                      image=p['image'], 
                      description=p['description'], 
                      category_id=p['category_id']
                      )
        db.session.add(pro)
        
    
    db.session.commit()