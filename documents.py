
## foreign keys

Here's an example:

python
Copy code
from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship

class Order(Base):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey('customers.id'))
    customer = relationship("Customer", back_populates="orders")

class Customer(Base):
    __tablename__ = 'customers'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    orders = relationship("Order", back_populates="customer")
In this example, the Order class has a customer_id attribute that is a foreign key referencing the id attribute of the Customer class. The ForeignKey object takes a string argument that specifies the name of the referenced table and column.

Additionally, the relationship method is used to define the inverse relationship between the Order and Customer classes. The back_populates argument is used to specify the name of the attribute on the related class that points back to the current class.

This creates a bidirectional relationship between Order and Customer classes where Customer has a collection of Order objects and each Order has a reference to a Customer object.





